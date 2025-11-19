from behave import given, when, then
from selenium import webdriver
from pages.login_page import LoginPage


@given('the user is on the Workday login page')
def step_open_login_page(context):
    context.driver = webdriver.Chrome()
    context.driver.get("https://impl.workday.com/wday/authgwy/onetp1/login.htmld?redirect=n")
    context.login_page = LoginPage(context.driver)


@when('the user enters valid credentials')
def step_enter_credentials(context):
    context.login_page.login("Testinguser", "pass-Workday@123")


@when('the user skips the Remember Device prompt')
def step_skip_remember_device(context):
    context.login_page.skip_remember_device()


@then('the user should be on the Workday home page')
def step_verify_home_page(context):
    expected_url = "https://impl.workday.com/onetp1/d/home.htmld"
    assert context.driver.current_url.startswith(expected_url), f"Expected URL: {expected_url}, but got: {context.driver.current_url}"


@then('the user should be logged into the Workday application')
def step_verify_login(context):
    assert "Workday" in context.driver.title


# Example feature steps
@given('I open the application')
def step_impl_open_app(context):
    context.driver = webdriver.Chrome()
    context.driver.get("https://impl.workday.com/wday/authgwy/onetp1/login.htmld?redirect=n")

@when('I perform an action')
def step_impl_action(context):
    # Example: login
    login_page = LoginPage(context.driver)
    login_page.login("Testinguser", "pass-Workday@123")

@then('I validate the result')
def step_impl_validate(context):
    assert "Workday" in context.driver.title
