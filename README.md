 # AI Selenium Cucumber BDD Zephyr Framework

## Overview
Python automation framework that combines Selenium WebDriver, Behave BDD, and a curated utility toolkit. The repository currently ships with the Saucedemo end-to-end checkout scenario and is ready for additional projects.

## Key Features
- Behave feature files with page-object style step helpers
- Selenium driver bootstrap for Chrome (default) and Firefox (via `BROWSER=firefox`)
- Centralised reporting (`reports/<project>` HTML summary and raw Behave JSON)
- Optional Allure integration (`allure-results/<project>`) when the CLI is installed
- Reusable utilities for data loading, self-healing, visual checks, and AI-driven test ideas

## Project Structure
```
features/                   # Shared Behave assets (if any)
projects/saucedemo/         # Example project bound to saucedemo.com
  features/                 # Feature files, step definitions, environment hooks
pages/                      # Page objects or shared page helpers
tests/test_runner.py        # Command-line entry point for Behave execution
reports/<project>/          # Generated summaries, zipped artifacts
allure-results/<project>/   # Allure JSON (requires Allure CLI to visualise)
utils/                      # Support modules (data loader, NLP generator, etc.)
```

## Prerequisites
- Python 3.11+
- Google Chrome (and driver) and/or Mozilla Firefox (and geckodriver)
- Optional: Allure CLI for HTML reports (`allure --version` should succeed)

## Installation
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` if project-specific environment variables are required (e.g., `GRID_URL`, credentials).

## Running Tests
Execute the unified runner and specify the project key:
```bash
python tests/test_runner.py --project saucedemo
```

To force Firefox instead of Chrome:
```bash
$env:BROWSER = "firefox"
python tests/test_runner.py --project saucedemo
Remove-Item Env:BROWSER
```

### Remote/Grid Execution
Set `GRID_URL` in the environment or `.env`; the driver factory automatically switches to `webdriver.Remote`.

## Reporting
- `reports/saucedemo/summary.html`: quick pass/error counts and metadata
- `reports/saucedemo/behave-report.json`: raw Behave output for downstream consumption
- `reports/saucedemo/latest_report_bundle.zip`: zipped artifacts for sharing
- `allure-results/saucedemo/`: ingest with `allure serve allure-results/saucedemo` after installing the Allure CLI

## Extending The Suite
1. Duplicate the project folder structure under `projects/<new_project>`.
2. Register the project in `config/project_registry.py` with its feature path and optional environment entries.
3. Model additional pages in `pages/` or within the project folder.
4. Leverage utilities in `utils/` to add self-healing, visual snapshots, or AI-generated tests.

## CI/CD Notes
- A sample GitHub Actions workflow lives under `.github/workflows/`.
- Dockerfile is provided for containerised execution; ensure browsers/drivers are installed during the image build.

## Support
Open an issue or reach out to the QA tooling team if you encounter driver compatibility, grid connectivity, or reporting integration questions.
