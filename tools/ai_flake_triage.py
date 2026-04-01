"""Command-line entry for AI-driven flake triage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from loguru import logger  # type: ignore
except ImportError:  # pragma: no cover
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

from utils.ai_flake_triage import AIFlakeTriage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyse a Behave JSON report for failure insights")
    parser.add_argument("json_report", help="Path to behave json.pretty report")
    parser.add_argument(
        "--telemetry",
        help="Path to self-healing telemetry JSON to enrich locator hints",
        default=None,
    )
    parser.add_argument(
        "--output-dir",
        help="Directory for triage JSON/Markdown output",
        default="reports/flake_triage",
    )
    parser.add_argument(
        "--project",
        help="Project identifier for metadata",
        default=None,
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional limit on number of failures to analyse",
        default=None,
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Echo computed insights to stdout",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    triage = AIFlakeTriage(telemetry_path=args.telemetry)
    insights = triage.triage(
        args.json_report,
        limit=args.limit,
        output_dir=args.output_dir,
        project=args.project,
    )

    if args.print_json:
        print(json.dumps(insights, indent=2))

    logger.info(f"Flake triage completed - failures analysed: {insights.get('failure_count', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
