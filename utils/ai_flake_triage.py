"""AI-inspired triage heuristics for Behave failure analysis."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

try:
    from loguru import logger  # type: ignore
except ImportError:  # pragma: no cover
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


_LOCATOR_FAILURE_PATTERNS = (
    "NoSuchElementException",
    "Unable to locate element",
    "invalid selector",
    "ElementNotInteractableException",
    "StaleElementReferenceException",
)
_WAIT_FAILURE_PATTERNS = (
    "TimeoutException",
    "timed out",
    "operation timed out",
)
_ASSERTION_PATTERNS = (
    "AssertionError",
    "assert",
    "did not match",
    "expected",
    "but was",
)


@dataclass
class FailureInsight:
    feature: str
    scenario: str
    step: str
    keyword: str
    status: str
    error_message: str
    classification: str
    suggestions: List[str]
    locator_hint: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "feature": self.feature,
            "scenario": self.scenario,
            "step": self.step,
            "keyword": self.keyword,
            "status": self.status,
            "error_message": self.error_message,
            "classification": self.classification,
            "suggestions": self.suggestions,
            "locator_hint": self.locator_hint,
        }


class AIFlakeTriage:
    """Generate structured heuristics for failed Behave scenarios."""

    def __init__(self, telemetry_path: Optional[Path | str] = None) -> None:
        self.telemetry_path = Path(telemetry_path).resolve() if telemetry_path else None
        self.telemetry = self._load_telemetry()

    def triage(
        self,
        report_path: Path | str,
        *,
        limit: Optional[int] = None,
        output_dir: Optional[Path | str] = None,
        project: Optional[str] = None,
    ) -> Dict[str, object]:
        """Analyse a Behave JSON report and persist insights."""

        report_path = Path(report_path).expanduser().resolve()
        if not report_path.exists():
            raise FileNotFoundError(f"Behave JSON report not found: {report_path}")

        failures = self._extract_failures(report_path)
        if limit is not None:
            failures = failures[:limit]

        statistics = self._summarise(failures)

        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "project": project,
            "source_report": str(report_path),
            "failure_count": len(failures),
            "classification_tally": statistics,
            "insights": [failure.to_dict() for failure in failures],
        }

        report_file: Optional[Path] = None
        markdown_file: Optional[Path] = None
        if output_dir:
            destination = Path(output_dir).expanduser().resolve()
            destination.mkdir(parents=True, exist_ok=True)
            stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            report_file = destination / f"flake_triage_{stamp}.json"
            report_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            markdown_file = destination / f"flake_triage_{stamp}.md"
            markdown_file.write_text(self._render_markdown(payload), encoding="utf-8")
            payload["report_path"] = str(report_file)
            payload["markdown_path"] = str(markdown_file)
            logger.info(f"Flake triage report written to {report_file}")
        return payload

    def _extract_failures(self, report_path: Path) -> List[FailureInsight]:
        raw = json.loads(report_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            features = [raw]
        else:
            features = raw

        insights: List[FailureInsight] = []
        for feature in features:
            feature_name = feature.get("name", "Unnamed Feature")
            for element in feature.get("elements", []):
                if element.get("type") != "scenario":
                    continue
                scenario_name = element.get("name", "Unnamed Scenario")
                failing_steps = [step for step in element.get("steps", []) if step.get("result", {}).get("status") == "failed"]
                for step in failing_steps:
                    result = step.get("result", {})
                    error_message = self._coalesce_error(result)
                    classification, suggestions = self._classify(error_message)
                    locator_hint = self._suggest_locator_hint(error_message)
                    insights.append(
                        FailureInsight(
                            feature=feature_name,
                            scenario=scenario_name,
                            step=step.get("name", ""),
                            keyword=step.get("keyword", ""),
                            status=result.get("status", "failed"),
                            error_message=error_message,
                            classification=classification,
                            suggestions=suggestions,
                            locator_hint=locator_hint,
                        )
                    )
        return insights

    def _classify(self, error_message: str) -> tuple[str, List[str]]:
        lower_error = error_message.lower()
        suggestions: List[str] = []

        if any(pattern.lower() in lower_error for pattern in _LOCATOR_FAILURE_PATTERNS):
            suggestions.append("Review the locator strategy or sync waits.")
            suggestions.append("Check self-healing telemetry for a suggested selector.")
            return "locator_failure", suggestions

        if any(pattern.lower() in lower_error for pattern in _WAIT_FAILURE_PATTERNS):
            suggestions.append("Increase explicit waits or verify the element's load state.")
            suggestions.append("Consider triggering prerequisite actions earlier.")
            return "synchronisation_timeout", suggestions

        if any(pattern.lower() in lower_error for pattern in _ASSERTION_PATTERNS):
            suggestions.append("Validate the expected value with recent UI changes.")
            suggestions.append("Review business logic or test data assumptions.")
            return "assertion_mismatch", suggestions

        if "connection" in lower_error or "timeout" in lower_error:
            suggestions.append("Verify network stability or remote driver availability.")
            return "infrastructure_issue", suggestions

        suggestions.append("Review stack trace for bespoke handling.")
        return "unknown", suggestions

    def _suggest_locator_hint(self, error_message: str) -> Optional[str]:
        if not self.telemetry:
            return None
        pattern = re.search(r"\((By\.[A-Z_]+),\s*'([^']+)'\)", error_message)
        if not pattern:
            return None
        locator_type = pattern.group(1).replace("By.", "").lower()
        locator_value = pattern.group(2)
        key = f"{locator_type}:{locator_value}"
        stats = self.telemetry.get(key)
        if not stats:
            return None
        suggested = stats.get("suggested_strategy")
        if suggested:
            return f"Telemetry recommends trying locator strategy '{suggested}' for value '{locator_value}'."
        return None

    @staticmethod
    def _coalesce_error(result: Dict[str, object]) -> str:
        message = (
            result.get("error_message")
            or result.get("message")
            or result.get("error")
            or ""
        )
        if isinstance(message, str) and message.strip():
            return message.strip()
        error = result.get("exception")
        if isinstance(error, dict):
            message = error.get("message") or error.get("error")
            if isinstance(message, str):
                return message.strip()
        return "No error message captured"

    @staticmethod
    def _summarise(failures: Iterable[FailureInsight]) -> Dict[str, int]:
        tally = Counter(failure.classification for failure in failures)
        return dict(tally)

    def _render_markdown(self, payload: Dict[str, object]) -> str:
        lines = [
            "# AI Flake Triage",
            "",
            f"Generated at: {payload.get('generated_at', '')}",
            f"Project: {payload.get('project', 'unknown')}",
            f"Source report: {payload.get('source_report', '')}",
            "",
            "## Classification Tally",
            json.dumps(payload.get("classification_tally", {}), indent=2),
            "",
            "## Failure Insights",
        ]
        for insight in payload.get("insights", []):
            lines.extend(
                [
                    f"### {insight['scenario']} -> {insight['step']}",
                    f"- Feature: {insight['feature']}",
                    f"- Step: {insight['keyword']} {insight['step']}",
                    f"- Classification: {insight['classification']}",
                    f"- Error: {insight['error_message']}",
                    f"- Suggestions: {', '.join(insight['suggestions'])}",
                ]
            )
            locator_hint = insight.get("locator_hint")
            if locator_hint:
                lines.append(f"- Telemetry: {locator_hint}")
            lines.append("")
        return "\n".join(lines).strip()

    def _load_telemetry(self) -> Dict[str, Dict[str, object]]:
        if not self.telemetry_path or not self.telemetry_path.exists():
            return {}
        try:
            return json.loads(self.telemetry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive parsing
            logger.warning(f"Unable to parse telemetry: {exc}")
            return {}


__all__ = ["AIFlakeTriage", "FailureInsight"]
