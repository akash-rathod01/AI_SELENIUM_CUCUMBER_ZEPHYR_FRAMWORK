# conftest.py for pytest tagging and filtering support
import pytest
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope='session')
def base_url():
    return os.getenv('BASE_URL')

# Add custom markers for test tagging
def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: mark test as smoke")
    config.addinivalue_line("markers", "regression: mark test as regression")
    config.addinivalue_line("markers", "critical: mark test as critical")

# Example usage in test:
# @pytest.mark.smoke
# def test_login():
#     ...
