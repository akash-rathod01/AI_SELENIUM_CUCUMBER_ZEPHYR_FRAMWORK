"""Manage generation of test execution reports and artifacts."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List
from zipfile import ZipFile

try:
    from loguru import logger  # type: ignore
except ImportError:  # pragma: no cover - fallback logging
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


class ReportManager:
    """Aggregate Allure, HTML, and archive artifacts for distribution."""

    def __init__(
        self,
        allure_results_dir: str = "allure-results",
        allure_report_dir: str = "reports/allure",
        html_report_path: str = "reports/summary.html",
        archive_path: str = "reports/latest_report_bundle.zip",
    ) -> None:
        self.allure_results_dir = Path(allure_results_dir)
        self.allure_report_dir = Path(allure_report_dir)
        self.html_report_path = Path(html_report_path)
        self.archive_path = Path(archive_path)
        self.html_report_path.parent.mkdir(parents=True, exist_ok=True)
        self.allure_report_dir.mkdir(parents=True, exist_ok=True)

    def generate_allure_report(self) -> None:
        """Invoke Allure CLI if available to create a rich HTML dashboard."""

        if not self.allure_results_dir.exists():
            logger.warning(f"Allure results directory missing: {self.allure_results_dir}")
            return

        allure_cli = shutil.which("allure")
        if not allure_cli:
            logger.warning("Allure CLI not found on PATH; skipping Allure report generation")
            return

        command = [
            allure_cli,
            "generate",
            str(self.allure_results_dir),
            "--clean",
            "-o",
            str(self.allure_report_dir),
        ]

        logger.info(f"Generating Allure report with command: {' '.join(command)}")
        try:
            subprocess.run(command, check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:  # pragma: no cover - external tool
            logger.error(
                f"Allure report generation failed: {exc.stderr.decode(errors='ignore')}"
            )

    def build_html_summary(self, summary: Dict) -> Path:
        """Render a lightweight HTML summary for quick sharing."""

        html = self._render_summary_html(summary)
        self.html_report_path.write_text(html, encoding="utf-8")
        logger.info(f"HTML summary written to {self.html_report_path}")
        return self.html_report_path

    def archive_artifacts(self, extra_files: Iterable[Path] | None = None) -> Path:
        """Bundle key artifacts (summary, Allure, JSON) into a zip for emailing."""

        files: List[Path] = [self.html_report_path]
        if self.allure_report_dir.exists():
            files.append(self.allure_report_dir)
        if extra_files:
            files.extend(extra_files)

        with ZipFile(self.archive_path, "w") as bundle:
            for item in files:
                if item.is_dir():
                    for path in item.rglob("*"):
                        if path.is_file():
                            bundle.write(path, path.relative_to(item.parent))
                elif item.exists():
                    bundle.write(item, item.name)
        logger.info(f"Packaged report artifacts into {self.archive_path}")
        return self.archive_path

    def _render_summary_html(self, summary: Dict) -> str:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
        scenarios = summary.get("scenarios", {})
        steps = summary.get("steps", {})
        failed_details = summary.get("failed_scenarios", [])

        rows = "".join(
            f"<tr><td>{scenario['name']}</td><td>{scenario['feature']}</td><td>{scenario['status']}</td></tr>"
            for scenario in failed_details
        )

        return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Automation Summary</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; }}
    h1 {{ color: #2c3e50; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 1.5rem; }}
    th, td {{ border: 1px solid #ccc; padding: 0.5rem; text-align: left; }}
    th {{ background: #f5f5f5; }}
    .metrics {{ display: flex; gap: 2rem; margin-top: 1rem; }}
    .metric {{ padding: 1rem; background: #eef2f5; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>Daily Automation Summary</h1>
  <p>Generated: {timestamp}</p>
  <div class=\"metrics\">
    <div class=\"metric\"><strong>Total Features</strong><br>{summary.get('total_features', 0)}</div>
    <div class=\"metric\"><strong>Total Scenarios</strong><br>{summary.get('total_scenarios', 0)}</div>
    <div class=\"metric\"><strong>Passed</strong><br>{scenarios.get('passed', 0)}</div>
    <div class=\"metric\"><strong>Failed</strong><br>{scenarios.get('failed', 0)}</div>
    <div class=\"metric\"><strong>Skipped</strong><br>{scenarios.get('skipped', 0)}</div>
  </div>
  <h2>Step Metrics</h2>
  <ul>
    <li>Passed: {steps.get('passed', 0)}</li>
    <li>Failed: {steps.get('failed', 0)}</li>
    <li>Skipped: {steps.get('skipped', 0)}</li>
  </ul>
  <h2>Failed Scenarios</h2>
  <table>
    <thead>
      <tr><th>Scenario</th><th>Feature</th><th>Status</th></tr>
    </thead>
    <tbody>
      {rows if rows else '<tr><td colspan="3">No failed scenarios</td></tr>'}
    </tbody>
  </table>
</body>
</html>
"""

    @staticmethod
    def load_json(path: Path) -> Dict:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
