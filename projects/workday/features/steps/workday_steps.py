import os

from behave import given, when, then
from selenium import webdriver

from pages.login_page import LoginPage


@given("the user launches the Workday portal")
def step_open_portal(context):
    driver = _build_driver()
    driver.get("https://impl.workday.com/wday/authgwy/onetp1/login.htmld?redirect=n")
    context.driver = driver
    context.login_page = LoginPage(driver)


@when("the user authenticates with valid Workday credentials")
def step_enter_credentials(context):
    context.login_page.login("Testinguser", "pass-Workday@123")


@when("the user dismisses the remember device overlay")
def step_skip_device(context):
    context.login_page.skip_remember_device()


@then("the Workday landing page should be displayed")
def step_validate_home(context):
    expected_url = "https://impl.workday.com/onetp1/d/home.htmld"
    assert context.driver.current_url.startswith(expected_url), (
        f"Expected URL prefix '{expected_url}' but saw '{context.driver.current_url}'"
    )
    assert "Workday" in context.driver.title


def _build_driver():
    # Hook for future Selenium Grid selection via environment variables.
    grid_url = os.getenv("GRID_URL")
    if grid_url:
        capabilities = webdriver.DesiredCapabilities.CHROME.copy()
        return webdriver.Remote(command_executor=grid_url, desired_capabilities=capabilities)
    return webdriver.Chrome()
