"""Generate scenario ideas from a stored blueprint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils import blueprint_repository
from utils.scenario_planner import ScenarioPlanner


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Produce scenario ideas from a blueprint.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--blueprint", help="Path to a blueprint JSON file.")
    source.add_argument("--project", help="Project key whose latest blueprint should be loaded.")
    parser.add_argument(
        "--output",
        help="Optional path to write the scenario ideas as JSON (defaults to stdout).",
    )
    return parser.parse_args(argv)


def load_blueprint(path: str | None, project: str | None):
    if path:
        return blueprint_repository.load_blueprint(path)
    assert project is not None  # guarded by argparse
    blueprint = blueprint_repository.load_latest(project)
    if blueprint is None:
        raise FileNotFoundError(f"No blueprint found for project '{project}'.")
    return blueprint


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    blueprint = load_blueprint(args.blueprint, args.project)
    planner = ScenarioPlanner(blueprint)
    ideas = planner.plan()

    payload = [
        {
            "title": idea.title,
            "requirement": idea.requirement,
            "source_url": idea.source_url,
            "priority": idea.priority,
            "tags": idea.tags,
        }
        for idea in ideas
    ]

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        print(f"Scenario ideas saved to {output_path}")
        return 0

    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
