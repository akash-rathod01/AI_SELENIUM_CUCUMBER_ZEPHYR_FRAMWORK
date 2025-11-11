# Onboarding and usage documentation

## AI Selenium Cucumber BDD Zephyr Framework

### Features
- Selenium-based web automation
- Cucumber BDD for readable test scenarios
- Self-healing locators
- Visual validation
- NLP-based test generation
- Advanced test data management
- Enterprise-grade logging (loguru)
- Allure reporting
- Parallel execution (pytest-xdist)
- Centralized config management (.env)
- Test tagging and filtering (pytest markers)
- Error handling utilities
- Docker and CI/CD ready

### Setup
1. Clone the repository
2. Install dependencies:
	```
	pip install -r requirements.txt
	```
3. Configure `.env` for your environment
4. Run tests:
	```
	pytest --maxfail=5 --disable-warnings --alluredir=allure-results
	```
5. Generate Allure report:
	```
	allure serve allure-results
	```

### Test Tagging & Filtering
- Use markers like `@pytest.mark.smoke`, `@pytest.mark.regression`, `@pytest.mark.critical` in your tests
- Run specific tags:
  ```
  pytest -m smoke
  ```

### Utilities
- See `utils/error_utils.py` for error handling
- See `utils/data_loader.py` for test data management

### CI/CD & Docker
- See `.github/workflows/python-app.yml` for GitHub Actions
- See `Dockerfile` for containerization

### Support
For onboarding, see comments in code and this README. For questions, contact your test architect.
# AI-Powered Selenium Python Automation Framework

This framework supports BDD with Behave, Page Object Model, AI-based features, CI/CD integration, and Zephyr for Jira sync.
