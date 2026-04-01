"""End-to-end scaffolding: blueprint -> scenario ideas -> feature files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils import blueprint_repository
from utils.automation_scaffolder import AutomationScaffolder
from utils.scenario_planner import ScenarioPlanner


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate feature assets from a blueprint.")
    parser.add_argument("--project", required=True, help="Project key (also used for output path).")
    parser.add_argument("--blueprint", help="Specific blueprint path (defaults to latest).")
    parser.add_argument("--feature-name", default="auto_blueprint", help="Output feature file name.")
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Enable LLM-backed scenario generation if configured in settings.",
    )
    return parser.parse_args(argv)


def load_blueprint(project: str, blueprint_path: str | None):
    if blueprint_path:
        return blueprint_repository.load_blueprint(blueprint_path)
    blueprint = blueprint_repository.load_latest(project)
    if blueprint is None:
        raise FileNotFoundError(f"No blueprint available for project '{project}'.")
    return blueprint


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    blueprint = load_blueprint(args.project, args.blueprint)
    planner = ScenarioPlanner(blueprint)
    ideas = planner.plan()
    if not ideas:
        raise SystemExit("No scenario ideas produced from blueprint; aborting.")

    scaffolder = AutomationScaffolder(args.project, feature_name=args.feature_name)
    result = scaffolder.scaffold(ideas, use_llm=args.use_llm)
    print(f"Feature written to {result.feature_path}")
    print(f"Step stubs written to {result.steps_path}")
    print(f"Generated {result.scenarios_generated} scenario drafts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
