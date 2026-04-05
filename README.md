# AI Selenium Cucumber BDD Zephyr Framework

## Overview
This repository provides a robust Python-based automation framework that integrates Selenium WebDriver, Behave BDD, and Zephyr for test management. It is designed to support scalable, maintainable, and AI-enhanced testing workflows.

## Key Features
- **Behavior-Driven Development (BDD)**: Write human-readable test scenarios using Behave.
- **Selenium WebDriver Integration**: Automate browser interactions with support for Chrome and Firefox.
- **AI-Powered Maintenance**: Includes tools for flaky test detection, locator healing, and automated diagnostics.
- **Comprehensive Reporting**: Generate detailed HTML and Allure reports for test execution.
- **Reusable Utilities**: Includes modules for data loading, visual validation, and scenario planning.
- **Multi-Project Support**: Easily manage and execute tests for multiple projects.

## Project Structure
```
features/                   # Shared Behave assets
projects/<project_name>/    # Project-specific features and steps
pages/                      # Page objects and shared helpers
tests/test_runner.py        # Unified test runner
reports/<project>/          # Test execution reports
allure-results/<project>/   # Allure report data
utils/                      # Utility modules
tools/                      # CLI tools for automation
```

## Prerequisites
- Python 3.11+
- Google Chrome or Mozilla Firefox (with respective drivers)
- Optional: Allure CLI for advanced reporting

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/akash-rathod01/AI_SELENIUM_CUCUMBER_ZEPHYR_FRAMWORK.git
   ```
2. Navigate to the project directory:
   ```bash
   cd AI_SELENIUM_CUCUMBER_ZEPHYR_FRAMWORK
   ```
3. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Running Tests
Run tests for a specific project:
```bash
python tests/test_runner.py --project <project_name>
```

Enable AI maintenance mode for enhanced diagnostics:
```bash
python tests/test_runner.py --project <project_name> --ai-maintenance
```

## Reporting
- **HTML Reports**: Generated in the `reports/<project>` directory.
- **Allure Reports**: Use the Allure CLI to visualize results:
  ```bash
  allure serve allure-results/<project>
  ```

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License.
