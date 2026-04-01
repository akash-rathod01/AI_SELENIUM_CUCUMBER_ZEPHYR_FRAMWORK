"""CLI utility to run the AI maintenance workflow on demand."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List, Optional

try:
    from loguru import logger  # type: ignore
except ImportError:  # pragma: no cover
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

from utils.ai_maintenance import AIMaintenanceManager


def _normalise_urls(urls: Optional[Iterable[str]]) -> List[str]:
    if not urls:
        return []
    normalised = []
    for url in urls:
        if not url:
            continue
        trimmed = url.strip()
        if trimmed:
            normalised.append(trimmed)
    return normalised


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AI maintenance workflow without executing tests")
    parser.add_argument(
        "--project",
        help="Project identifier used for report metadata",
        default=None,
    )
    parser.add_argument(
        "--run-summary",
        help="Optional path to a JSON run summary to include in the maintenance report",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--base-url",
        action="append",
        help="Seed URL for broken-link diagnostics (may be used multiple times)",
    )
    parser.add_argument(
        "--snapshot-label",
        help="Custom label for the generated snapshot",
        default=None,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    run_summary = {}
    if args.run_summary:
        summary_path = Path(args.run_summary).expanduser().resolve()
        if summary_path.exists():
            try:
                run_summary = json.loads(summary_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                logger.error(f"Unable to parse run summary JSON ({summary_path}): {exc}")
        else:
            logger.warning(f"Run summary file not found: {summary_path}")

    manager = AIMaintenanceManager()
    base_urls = _normalise_urls(args.base_url)
    report = manager.perform_maintenance(
        project=args.project,
        run_summary=run_summary or None,
        base_urls=base_urls or None,
        snapshot_label=args.snapshot_label,
    )

    logger.info(
        f"AI maintenance completed - report={report.get('report_path', 'n/a')}, snapshot={report.get('snapshot', 'n/a')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
