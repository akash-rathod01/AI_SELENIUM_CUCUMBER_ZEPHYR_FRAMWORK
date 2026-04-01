"""Utility for generating Allure dashboards for every registered project."""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from config.project_registry import ProjectDefinition, get_project, list_projects
from reporting.report_manager import ReportManager


@dataclass(frozen=True)
class DashboardEntry:
    project: ProjectDefinition
    report_path: Optional[Path]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Allure dashboards for one or all registered projects."
    )
    parser.add_argument(
        "--project",
        help="Optional project key; omit to build dashboards for every project.",
        default=None,
    )
    parser.add_argument(
        "--output",
        help="Override path for consolidated dashboard index (default: reports/allure_dashboard.html).",
        default="reports/allure_dashboard.html",
    )
    args = parser.parse_args()

    if not _validate_allure_cli():
        return 1

    projects = _projects_to_process(args.project)
    entries = []
    for project in projects:
        entry = _generate_for_project(project)
        entries.append(entry)

    _build_dashboard_index(entries, Path(args.output))
    return 0


def _validate_allure_cli() -> bool:
    if shutil.which("allure"):
        return True
    print("Allure CLI was not found on PATH. Install Allure before running this script.")
    return False


def _projects_to_process(project_key: Optional[str]) -> Iterable[ProjectDefinition]:
    if project_key:
        return [get_project(project_key)]
    return list_projects()


def _generate_for_project(project: ProjectDefinition) -> DashboardEntry:
    results_dir = Path("allure-results") / project.key
    report_dir = Path("reports") / project.key / "allure"
    summary_path = report_dir.parent / "summary.html"
    archive_path = report_dir.parent / "latest_report_bundle.zip"

    if not results_dir.exists():
        print(f"Skipping {project.key}; results directory not found at {results_dir}")
        return DashboardEntry(project=project, report_path=None)

    manager = ReportManager(
        allure_results_dir=str(results_dir),
        allure_report_dir=str(report_dir),
        html_report_path=str(summary_path),
        archive_path=str(archive_path),
    )
    manager.generate_allure_report()

    index_html = report_dir / "index.html"
    if not index_html.exists():
        print(f"Generated report for {project.key} but missing {index_html}")
        return DashboardEntry(project=project, report_path=None)

    print(f"Allure dashboard ready for {project.key} at {index_html}")
    return DashboardEntry(project=project, report_path=index_html)


def _build_dashboard_index(entries: Iterable[DashboardEntry], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    links = []
    for entry in entries:
        if entry.report_path:
            rel_path = entry.report_path.as_posix()
            links.append(
                f"      <li><a href=\"{rel_path}\" target=\"_blank\">{entry.project.name} ({entry.project.key})</a></li>"
            )
        else:
            links.append(
                f"      <li>{entry.project.name} ({entry.project.key}) - report unavailable</li>"
            )
    links_html = "\n".join(links)

    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Allure Dashboards</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; }}
    h1 {{ color: #2c3e50; }}
    ul {{ line-height: 1.8; }}
  </style>
</head>
<body>
  <h1>Project Allure Dashboards</h1>
  <p>Select a project below to open its Allure report in a new tab.</p>
  <ul>
{links_html}
  </ul>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")
    print(f"Dashboard index written to {output_path}")


if __name__ == "__main__":
    raise SystemExit(main())
