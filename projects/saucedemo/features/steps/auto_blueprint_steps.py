from __future__ import annotations

from behave import given, when, then
import requests
from bs4 import BeautifulSoup


@given("the application is prepared")
def step_prepare_app(context):
    context.target_url = "https://www.saucedemo.com/"


@when(
    "Ensure the page at https://www.saucedemo.com responds with HTTP 200 and displays the title 'Swag Labs'."
)
def step_fetch_metadata(context):
    response = requests.get(context.target_url, timeout=15)
    context.http_status = response.status_code
    soup = BeautifulSoup(response.text, "html.parser")
    title_el = soup.find("title")
    context.page_title = title_el.text.strip() if title_el else ""


@then("the expected outcome should be verified")
def step_verify_metadata(context):
    assert context.http_status == 200, f"Expected HTTP 200 but saw {context.http_status}"
    assert context.page_title == "Swag Labs", f"Expected title 'Swag Labs' but saw '{context.page_title}'"
