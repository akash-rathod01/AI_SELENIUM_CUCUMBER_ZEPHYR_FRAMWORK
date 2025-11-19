"""Unified entry point for running Behave suites with rich reporting."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
	from loguru import logger  # type: ignore
except ImportError:  # pragma: no cover - fallback for minimal environments
	import logging

	logging.basicConfig(level=logging.INFO)
	logger = logging.getLogger(__name__)

from dotenv import load_dotenv

from config.project_registry import ProjectDefinition, get_project, list_projects
from reporting.emailer import ReportEmailer
from reporting.report_manager import ReportManager
from utils.ai_analytics import TestRunAnalytics


def run_behave(tags: Optional[str] = None, dry_run: bool = False, project_key: Optional[str] = None) -> int:
	project = _resolve_project(project_key)
	_setup_env(project)

	features_path = project.features_path
	if not features_path.exists():
		raise FileNotFoundError(f"Features directory not found for project '{project.key}': {features_path}")

	reports_dir = Path("reports") / project.key
	reports_dir.mkdir(parents=True, exist_ok=True)
	json_report = reports_dir / "behave-report.json"
	allure_results = Path("allure-results") / project.key
	allure_results.mkdir(parents=True, exist_ok=True)

	command = [
		"behave",
		str(features_path),
		"-f",
		"allure_behave.formatter:AllureFormatter",
		"-o",
		str(allure_results),
		"-f",
		"json.pretty",
		"-o",
		str(json_report),
	]

	if tags:
		command.extend(["--tags", tags])
	if dry_run:
		command.append("--dry-run")

	logger.info(
		"Executing Behave suite",
		command=" ".join(command),
		project=project.key,
		features=str(features_path),
	)
	result = subprocess.run(command, check=False)

	summary = build_summary(json_report)
	summary["return_code"] = result.returncode
	summary["project"] = project.key
	summary["project_name"] = project.name

	analytics = TestRunAnalytics()
	analytics.record_run(run_summary(summary))

	report_manager = ReportManager(
		allure_results_dir=str(allure_results),
		allure_report_dir=str(reports_dir / "allure"),
		html_report_path=str(reports_dir / "summary.html"),
		archive_path=str(reports_dir / "latest_report_bundle.zip"),
	)
	report_manager.generate_allure_report()
	html_summary_path = report_manager.build_html_summary(summary)
	archive_path = report_manager.archive_artifacts(extra_files=[json_report])

	_maybe_send_email(summary, [html_summary_path, archive_path])

	if summary.get("scenarios", {}).get("failed", 0) > 0:
		logger.warning("Some scenarios failed; see reports for details")
	else:
		logger.info("All scenarios passed")

	return result.returncode


def _setup_env(project: ProjectDefinition) -> None:
	if project.env_file and project.env_file.exists():
		load_dotenv(dotenv_path=project.env_file, override=True)
		logger.info("Loaded project environment", project=project.key, env_file=str(project.env_file))
	else:
		logger.debug("No project-specific .env file found", project=project.key)


def _resolve_project(project_key: Optional[str]) -> ProjectDefinition:
	try:
		return get_project(project_key)
	except ValueError as exc:
		available = ", ".join(p.key for p in list_projects())
		raise SystemExit(f"{exc}. Registered projects: {available}") from exc


def _print_projects() -> None:
	print("Registered automation projects:")
	for project in list_projects():
		features = project.features_path
		if project.features_path.is_absolute():
			try:
				features = project.features_path.relative_to(Path.cwd())
			except ValueError:
				features = project.features_path
		print(f"- {project.key}: {project.name} ({features})")


def build_summary(json_report: Path) -> Dict:
	if not json_report.exists():
		logger.warning("JSON report missing; returning empty summary", path=str(json_report))
		return default_summary()

	data = json.loads(json_report.read_text(encoding="utf-8"))
	if not isinstance(data, list):  # pragma: no cover - defensive
		data = [data]

	total_features = len(data)
	total_scenarios = 0
	scenario_passed = 0
	scenario_failed = 0
	scenario_skipped = 0
	steps_passed = steps_failed = steps_skipped = 0
	failed_scenarios: List[Dict] = []
	total_duration = 0.0

	for feature in data:
		feature_name = feature.get("name", "Unnamed Feature")
		for element in feature.get("elements", []):
			if element.get("type") != "scenario":
				continue
			total_scenarios += 1
			status, step_stats, duration = _scenario_status(element)
			total_duration += duration
			steps_passed += step_stats["passed"]
			steps_failed += step_stats["failed"]
			steps_skipped += step_stats["skipped"]

			if status == "passed":
				scenario_passed += 1
			elif status == "failed":
				scenario_failed += 1
				failed_scenarios.append(
					{
						"feature": feature_name,
						"name": element.get("name", "Unnamed Scenario"),
						"status": status,
					}
				)
			else:
				scenario_skipped += 1

	return {
		"generated_at": datetime.utcnow().isoformat(),
		"total_features": total_features,
		"total_scenarios": total_scenarios,
		"duration_seconds": round(total_duration, 2),
		"scenarios": {
			"passed": scenario_passed,
			"failed": scenario_failed,
			"skipped": scenario_skipped,
		},
		"steps": {
			"passed": steps_passed,
			"failed": steps_failed,
			"skipped": steps_skipped,
		},
		"failed_scenarios": failed_scenarios,
	}


def _scenario_status(element: Dict) -> tuple[str, Dict[str, int], float]:
	steps = element.get("steps", [])
	status = "passed"
	stats = {"passed": 0, "failed": 0, "skipped": 0}
	duration = 0.0
	for step in steps:
		result = step.get("result", {})
		step_status = result.get("status", "skipped")
		duration += result.get("duration", 0)
		if step_status == "failed":
			status = "failed"
			stats["failed"] += 1
		elif step_status == "passed":
			stats["passed"] += 1
		else:
			if status != "failed":
				status = "skipped"
			stats["skipped"] += 1
	return status, stats, duration


def default_summary() -> Dict:
	return {
		"generated_at": datetime.utcnow().isoformat(),
		"total_features": 0,
		"total_scenarios": 0,
		"duration_seconds": 0.0,
		"scenarios": {"passed": 0, "failed": 0, "skipped": 0},
		"steps": {"passed": 0, "failed": 0, "skipped": 0},
		"failed_scenarios": [],
	}


def run_summary(summary: Dict) -> Dict:
	return {
		"run_id": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
		"timestamp": summary.get("generated_at"),
		"duration": summary.get("duration_seconds", 0.0),
		"passed": summary.get("scenarios", {}).get("passed", 0),
		"failed": summary.get("scenarios", {}).get("failed", 0),
		"skipped": summary.get("scenarios", {}).get("skipped", 0),
		"failed_tests": [item.get("name") for item in summary.get("failed_scenarios", [])],
		"project": summary.get("project"),
	}


def _maybe_send_email(summary: Dict, attachments: List[Path]) -> None:
	emailer = ReportEmailer()
	body = (
		f"Automation run completed for project: {summary.get('project_name', summary.get('project', 'core'))}.\n"
		f"Total scenarios: {summary.get('total_scenarios', 0)}\n"
		f"Passed: {summary.get('scenarios', {}).get('passed', 0)}\n"
		f"Failed: {summary.get('scenarios', {}).get('failed', 0)}\n"
	)
	try:
		emailer.send("Automation Execution Summary", body, attachments)
	except Exception as exc:  # pragma: no cover - external dependency
		logger.error("Failed to send report email", error=str(exc))


def main() -> int:
	parser = argparse.ArgumentParser(description="Run Behave suites with reporting")
	parser.add_argument("--tags", help="Behave tags to include", default=None)
	parser.add_argument("--dry-run", action="store_true", help="Run in Behave dry-run mode")
	parser.add_argument(
		"--project",
		help="Registered project key (see config.project_registry). Default uses core features.",
		default=None,
	)
	parser.add_argument(
		"--list-projects",
		action="store_true",
		help="List all registered project keys and exit",
	)
	args = parser.parse_args()
	if args.list_projects:
		_print_projects()
		return 0
	return run_behave(tags=args.tags, dry_run=args.dry_run, project_key=args.project)


if __name__ == "__main__":
	raise SystemExit(main())
