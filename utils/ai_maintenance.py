"""AI-first maintenance utilities for automating framework self-care tasks."""

from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

try:  # Align logging strategy with rest of the codebase
    from loguru import logger  # type: ignore
except ImportError:  # pragma: no cover - fallback for pared-down environments
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

from utils.ai_analytics import TestRunAnalytics
from utils.ai_flake_triage import AIFlakeTriage
from utils.self_healing import SelfHealingLocator
from utils.web_crawler import WebCrawler


class AIMaintenanceManager:
    """Orchestrates AI-assisted resilience tooling for the automation platform."""

    DEFAULT_SNAPSHOT_TARGETS = (
        "features",
        "pages",
        "projects",
        "utils",
        "tests",
        "config",
    )

    def __init__(
        self,
        project_root: Optional[Path | str] = None,
        telemetry_path: Optional[Path | str] = None,
    ) -> None:
        self.project_root = Path(project_root or Path(__file__).resolve().parents[1]).resolve()
        self.telemetry_path = Path(telemetry_path or (self.project_root / "self_healing_metrics.json"))
        self.snapshots_dir = self.project_root / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.maintenance_dir = self.project_root / "reports" / "maintenance"
        self.maintenance_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Safety net utilities
    # ------------------------------------------------------------------
    def create_snapshot(
        self,
        label: Optional[str] = None,
        *,
        include: Optional[Iterable[str]] = None,
        inject_manifest: bool = True,
    ) -> Path:
        """Create a zip snapshot of key automation assets for disaster recovery."""

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        slug = self._slugify(label) if label else "snapshot"
        archive_name = f"{timestamp}_{slug}.zip"
        archive_path = self.snapshots_dir / archive_name

        targets = include or self.DEFAULT_SNAPSHOT_TARGETS
        targets = tuple(dict.fromkeys(targets))  # remove duplicates while preserving order

        manifest = {
            "created_at": datetime.utcnow().isoformat() + "Z",
            "label": label or slug,
            "project_root": str(self.project_root),
            "included_paths": [],
        }

        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_stream:
            for relative in targets:
                resolved = (self.project_root / relative).resolve()
                if not resolved.exists():
                    logger.debug(f"Snapshot skip - missing path: {resolved}")
                    continue
                manifest["included_paths"].append(relative)
                if resolved.is_file():
                    zip_stream.write(resolved, resolved.relative_to(self.project_root))
                    continue
                for candidate in resolved.rglob("*"):
                    if candidate.is_file():
                        arcname = candidate.relative_to(self.project_root)
                        zip_stream.write(candidate, arcname)
            if inject_manifest:
                zip_stream.writestr("SNAPSHOT_MANIFEST.json", json.dumps(manifest, indent=2))

        logger.info(f"Snapshot created at {archive_path}")
        return archive_path

    def restore_snapshot(self, snapshot: Path | str, *, restore_to: Optional[Path | str] = None) -> Path:
        """Extract a snapshot to a safe location (does not overwrite in-place by default)."""

        snapshot_path = Path(snapshot).expanduser().resolve()
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")

        destination = Path(restore_to or (self.snapshots_dir / f"restore_{snapshot_path.stem}"))
        destination = destination.resolve()
        destination.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(snapshot_path, "r") as zip_stream:
            zip_stream.extractall(destination)

        logger.info(f"Snapshot restored from {snapshot_path} to {destination}")
        return destination

    # ------------------------------------------------------------------
    # AI telemetry & healing
    # ------------------------------------------------------------------
    def locator_health(self) -> List[Dict[str, object]]:
        """Return locator telemetry sorted by most problematic selectors."""

        if not self.telemetry_path.exists():
            return []
        telemetry = json.loads(self.telemetry_path.read_text(encoding="utf-8"))
        insights: List[Dict[str, object]] = []
        for locator_key, stats in telemetry.items():
            failures = int(stats.get("failure", 0))
            healed = int(stats.get("healed", 0))
            if failures == 0 and healed == 0:
                continue
            insights.append(
                {
                    "locator": locator_key,
                    "failures": failures,
                    "healed": healed,
                    "last_strategy": stats.get("last_strategy"),
                    "suggested_strategy": stats.get("suggested_strategy"),
                    "last_update": stats.get("last_update"),
                }
            )
        insights.sort(key=lambda item: (item.get("failures", 0), item.get("healed", 0)), reverse=True)
        return insights

    def apply_self_healing(
        self,
        driver,
        locators: Iterable[tuple[str, str]],
        *,
        screenshot_test_name: Optional[str] = None,
    ) -> Dict[str, str]:
        """Attempt to resolve failing locators using the existing self-healing engine."""

        healer = SelfHealingLocator(driver, telemetry_path=str(self.telemetry_path))
        results: Dict[str, str] = {}
        for locator_type, locator_value in locators:
            try:
                healer.find_element(locator_type, locator_value, test_name=screenshot_test_name)
                results[f"{locator_type}:{locator_value}"] = "healed"
            except Exception as exc:  # broad catch keeps loop resilient
                results[f"{locator_type}:{locator_value}"] = f"failed: {exc}"  # pragma: no cover - driver dependent
        return results

    # ------------------------------------------------------------------
    # Observability & auto diagnostics
    # ------------------------------------------------------------------
    def build_health_report(
        self,
        *,
        project: Optional[str] = None,
        run_summary: Optional[Dict[str, object]] = None,
        base_urls: Optional[Iterable[str]] = None,
        max_pages: int = 50,
        min_failures_for_flaky: int = 2,
    ) -> Dict[str, object]:
        """Aggregate AI insights into a structured maintenance report."""

        analytics = TestRunAnalytics()
        anomalies = analytics.detect_anomalies()
        if hasattr(anomalies, "to_dict"):
            anomalies_blob = anomalies.to_dict(orient="records")
        else:
            anomalies_blob = anomalies

        flaky_candidates = analytics.flaky_test_candidates(min_failures=min_failures_for_flaky)
        if hasattr(flaky_candidates, "to_dict"):
            flaky_blob = flaky_candidates.to_dict(orient="records")
        else:
            flaky_blob = flaky_candidates

        retry_recommendations = analytics.retry_recommendations()

        locator_insights = self.locator_health()

        link_diagnostics: Dict[str, object] = {}
        for url in base_urls or []:
            try:
                crawler = WebCrawler(url, max_depth=1, max_pages=max_pages, respect_robots=False)
                crawl_result = crawler.crawl()
                link_diagnostics[url] = {
                    "broken_links": crawl_result.get("broken_links", {}),
                    "errors": crawl_result.get("errors", {}),
                    "statistics": crawl_result.get("statistics", {}),
                }
            except Exception as exc:  # pragma: no cover - network dependent
                link_diagnostics[url] = {"error": str(exc)}

        report = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "project": project,
            "run_summary": run_summary or {},
            "anomaly_candidates": anomalies_blob or [],
            "flaky_tests": flaky_blob or [],
            "retry_recommendations": retry_recommendations or [],
            "locator_health": locator_insights,
            "link_diagnostics": link_diagnostics,
        }
        return report

    def perform_maintenance(
        self,
        *,
        project: Optional[str] = None,
        run_summary: Optional[Dict[str, object]] = None,
        base_urls: Optional[Iterable[str]] = None,
        snapshot_label: Optional[str] = None,
        json_report_path: Optional[Path | str] = None,
    ) -> Dict[str, object]:
        """Generate a maintenance snapshot and persist the consolidated AI report."""

        snapshot_path = self.create_snapshot(label=snapshot_label or f"{project}_post_run")
        report = self.build_health_report(
            project=project,
            run_summary=run_summary,
            base_urls=base_urls,
        )
        report["snapshot"] = str(snapshot_path)

        if json_report_path and Path(json_report_path).exists():
            triage_output_dir = self.maintenance_dir / "flake_triage"
            triage = AIFlakeTriage(telemetry_path=self.telemetry_path)
            triage_payload = triage.triage(
                json_report_path,
                output_dir=triage_output_dir,
                project=project,
            )
            report["flake_triage"] = {
                "report_path": triage_payload.get("report_path"),
                "markdown_path": triage_payload.get("markdown_path"),
                "classification_tally": triage_payload.get("classification_tally"),
                "failure_count": triage_payload.get("failure_count"),
            }

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_path = self.maintenance_dir / f"maintenance_{timestamp}.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["report_path"] = str(report_path)

        summary_path = report_path.with_suffix(".md")
        summary_path.write_text(self._render_markdown_summary(report), encoding="utf-8")
        report["markdown_path"] = str(summary_path)

        logger.info(f"AI maintenance artifacts generated at {report_path}")
        return report

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _slugify(value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_")
        return cleaned or "snapshot"

    def _render_markdown_summary(self, report: Dict[str, object]) -> str:
        """Provide a human-readable maintenance digest."""

        lines = [
            f"# AI Maintenance Summary",
            "",
            f"Generated at: {report.get('generated_at', '')}",
            f"Project: {report.get('project', 'unknown')}",
            f"Snapshot: {report.get('snapshot', 'n/a')}",
            "",
            "## Run Overview",
            json.dumps(report.get("run_summary", {}), indent=2),
            "",
            "## Flaky Test Candidates",
            json.dumps(report.get("flaky_tests", []), indent=2),
            "",
            "## Anomaly Candidates",
            json.dumps(report.get("anomaly_candidates", []), indent=2),
            "",
            "## Retry Recommendations",
            json.dumps(report.get("retry_recommendations", []), indent=2),
            "",
            "## Locator Health",
            json.dumps(report.get("locator_health", []), indent=2),
            "",
            "## Link Diagnostics",
            json.dumps(report.get("link_diagnostics", {}), indent=2),
            "",
        ]
        return "\n".join(lines)


__all__ = ["AIMaintenanceManager"]
