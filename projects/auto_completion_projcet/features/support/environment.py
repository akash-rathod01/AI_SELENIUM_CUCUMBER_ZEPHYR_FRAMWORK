"""Behave hooks for auto_completion_projcet."""

from __future__ import annotations

import os
from typing import Any

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from pages.dotesthere_page import DoTestHerePage


DEFAULT_IMPLICIT_WAIT = int(os.getenv("SELENIUM_IMPLICIT_WAIT", "0"))
EXPLICIT_WAIT_SECONDS = int(os.getenv("SELENIUM_EXPLICIT_WAIT", "15"))


def _build_driver() -> webdriver.Remote:
    """Instantiate a Selenium driver based on environment variables."""
    browser = os.getenv("BROWSER", "firefox").lower()
    headless = os.getenv("HEADLESS", "true").lower() in {"1", "true", "yes"}

    if browser == "chrome":
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=options)
    else:
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument("-headless")
        options.set_preference("dom.webnotifications.enabled", False)
        driver = webdriver.Firefox(options=options)
        driver.set_window_size(1920, 1080)

    if DEFAULT_IMPLICIT_WAIT:
        driver.implicitly_wait(DEFAULT_IMPLICIT_WAIT)

    return driver


def before_scenario(context: Any, scenario: Any) -> None:
    context.driver = _build_driver()
    context.wait = WebDriverWait(context.driver, EXPLICIT_WAIT_SECONDS)
    context.page = DoTestHerePage(context.driver, context.wait)
    context.page.navigate_to_home()


def after_scenario(context: Any, scenario: Any) -> None:  # pragma: no cover - Behave hook
    driver = getattr(context, "driver", None)
    if driver:
        driver.quit()
    for attr in ("driver", "wait", "page"):
        if hasattr(context, attr):
            setattr(context, attr, None)
