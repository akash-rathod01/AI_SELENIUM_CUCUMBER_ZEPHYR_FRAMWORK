"""Command-line entry point for generating page blueprints via the crawler."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils import blueprint_repository
from utils.web_crawler import WebCrawler


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a blueprint from a target URL.")
    parser.add_argument("--url", required=True, help="Seed URL to start crawling from.")
    parser.add_argument("--project", required=True, help="Project key used for storage.")
    parser.add_argument("--max-depth", type=int, default=2, help="Maximum crawl depth.")
    parser.add_argument(
        "--include-domains",
        nargs="*",
        default=None,
        help="Restrict crawl to these domains (defaults to the seed domain).",
    )
    parser.add_argument(
        "--exclude-paths",
        nargs="*",
        default=None,
        help="Paths to skip (prefix match, e.g. /logout).",
    )
    parser.add_argument("--stdout", action="store_true", help="Print blueprint JSON to stdout instead of saving.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    crawler = WebCrawler(
        base_url=args.url,
        max_depth=args.max_depth,
        include_domains=args.include_domains,
        exclude_paths=args.exclude_paths,
    )
    blueprint = crawler.crawl()
    blueprint["project"] = args.project
    blueprint["generated_at"] = datetime.utcnow().isoformat() + "Z"

    if args.stdout:
        json.dump(blueprint, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    path = blueprint_repository.save_blueprint(args.project, blueprint)
    print(f"Blueprint saved to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
