"""Turn scenario ideas into feature files and step stubs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

from utils.scenario_planner import ScenarioIdea
from utils.nlp_test_generator import NLPTestGenerator, export_to_gherkin


@dataclass
class ScaffoldResult:
    feature_path: Path
    steps_path: Path
    scenarios_generated: int


class AutomationScaffolder:
    """Generate Behave assets from scenario ideas using the NLP generator."""

    def __init__(self, project: str, *, feature_name: str = "auto_blueprint") -> None:
        self.project = project
        self.feature_name = feature_name
        self.generator = NLPTestGenerator()

    def scaffold(self, ideas: Iterable[ScenarioIdea], *, use_llm: bool | None = None) -> ScaffoldResult:
        scenarios = []
        for idea in ideas:
            scenarios.extend(self.generator.generate(idea.requirement, use_llm=use_llm))

        if not scenarios:
            raise ValueError("No scenarios generated from supplied ideas.")

        feature_dir = Path("projects") / self.project / "features"
        steps_dir = feature_dir / "steps"
        feature_dir.mkdir(parents=True, exist_ok=True)
        steps_dir.mkdir(parents=True, exist_ok=True)

        feature_path = feature_dir / f"{self.feature_name}.feature"
        steps_path = steps_dir / f"{self.feature_name}_steps.py"

        feature_content = export_to_gherkin(scenarios)
        feature_path.write_text(feature_content + "\n", encoding="utf-8")

        unique_steps = self._collect_unique_steps(scenarios)
        steps_content = self._build_steps_module(unique_steps)
        steps_path.write_text(steps_content + "\n", encoding="utf-8")

        return ScaffoldResult(
            feature_path=feature_path.resolve(),
            steps_path=steps_path.resolve(),
            scenarios_generated=len(scenarios),
        )

    @staticmethod
    def _collect_unique_steps(scenarios) -> List[str]:
        seen = []
        for scenario in scenarios:
            for step in scenario.steps:
                if step not in seen:
                    seen.append(step)
        return seen

    def _build_steps_module(self, steps: Iterable[str]) -> str:
        lines = [
            "from behave import given, when, then",
            "",
        ]
        for step in steps:
            decorator, expression = self._step_decorator_and_expression(step)
            lines.append(f"@{decorator}(\"{expression}\")")
            lines.append(f"def step_impl(context):")
            lines.append("    raise NotImplementedError('Auto-generated step stub')")
            lines.append("")
        return "\n".join(lines).strip()

    @staticmethod
    def _step_decorator_and_expression(step: str) -> Tuple[str, str]:
        lowered = step.lower()
        if lowered.startswith("given"):
            decorator = "given"
            remainder = step[6:].strip()
        elif lowered.startswith("when"):
            decorator = "when"
            remainder = step[4:].strip()
        elif lowered.startswith("then"):
            decorator = "then"
            remainder = step[4:].strip()
        else:
            decorator = "when"
            remainder = step
        expression = AutomationScaffolder._normalise_expression(remainder)
        return decorator, expression

    @staticmethod
    def _normalise_expression(step_text: str) -> str:
        cleaned = re.sub(r"[\s]+", " ", step_text.strip())
        cleaned = cleaned.replace('"', '\\"')
        return cleaned or "step"
