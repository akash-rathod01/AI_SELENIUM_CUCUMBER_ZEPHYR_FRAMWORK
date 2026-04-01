import os
import time
from typing import Dict, Tuple

from behave import given, when, then, step
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.common.exceptions import NoAlertPresentException, TimeoutException


ITEM_ADD_BUTTONS: Dict[str, str] = {
    "Sauce Labs Backpack": "add-to-cart-sauce-labs-backpack",
    "Sauce Labs Bolt T-Shirt": "add-to-cart-sauce-labs-bolt-t-shirt",
    "Sauce Labs Onesie": "add-to-cart-sauce-labs-onesie",
    "Sauce Labs Bike Light": "add-to-cart-sauce-labs-bike-light",
}

REMOVE_BUTTON_IDS: Dict[str, str] = {
    name: add_id.replace("add-to-cart", "remove") for name, add_id in ITEM_ADD_BUTTONS.items()
}

DEFAULT_PAUSE = float(os.getenv("STEP_PAUSE", "3"))


@given("a Saucedemo user opens the login page")
def step_open_login(context):
    context.driver = _build_driver()
    context.driver.get("https://www.saucedemo.com/")
    context.wait = WebDriverWait(context.driver, 15)
    _pause()


@when("the user signs in with standard credentials")
def step_login(context):
    username = os.getenv("SAUCEDEMO_USERNAME", "standard_user")
    password = os.getenv("SAUCEDEMO_PASSWORD", "secret_sauce")
    context.wait.until(EC.visibility_of_element_located((By.ID, "user-name"))).send_keys(username)
    context.driver.find_element(By.ID, "password").send_keys(password)
    context.driver.find_element(By.ID, "login-button").click()
    _dismiss_password_security_alert(context.driver)
    context.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "inventory_list")))
    _pause()


@when("the user adds the following items to the cart:")
@when("the user adds the following items to the cart")
def step_add_multiple_items(context):
    for index, row in enumerate(context.table, start=1):
        item_name = row["item"].strip()
        _add_item_to_cart(context, item_name)
        _wait_for_cart_badge(context, str(index))
    _pause()


@when('the user removes "{item_name}" from the catalog')
def step_remove_item(context, item_name: str):
    _remove_item_from_cart(context, item_name.strip())
    _pause()


@when('the cart badge should display "{count}"')
@then('the cart badge should display "{count}"')
def step_verify_cart_badge(context, count: str):
    _wait_for_cart_badge(context, count)
    badge = context.driver.find_element(By.CLASS_NAME, "shopping_cart_badge")
    assert badge.text == count, f"Expected cart badge to show {count} items but saw '{badge.text}'"
    _pause()


@step("the user opens the cart")
def step_open_cart(context):
    context.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "shopping_cart_link"))).click()
    context.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "cart_list")))
    _pause()


@step("the user proceeds to checkout")
def step_proceed_to_checkout(context):
    context.wait.until(EC.element_to_be_clickable((By.ID, "checkout"))).click()
    context.wait.until(EC.visibility_of_element_located((By.ID, "first-name")))
    _pause()


@step("the user submits checkout information:")
@step("the user submits checkout information")
def step_submit_checkout_information(context):
    data_row = context.table[0]
    context.driver.find_element(By.ID, "first-name").send_keys(data_row["first_name"])
    context.driver.find_element(By.ID, "last-name").send_keys(data_row["last_name"])
    context.driver.find_element(By.ID, "postal-code").send_keys(data_row["postal_code"])
    context.wait.until(EC.element_to_be_clickable((By.ID, "continue"))).click()
    context.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "summary_info")))
    _pause()


@step("the order should complete successfully")
def step_complete_order(context):
    context.wait.until(EC.element_to_be_clickable((By.ID, "finish"))).click()
    header = context.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "complete-header")))
    message = header.text.strip()
    assert message == "Thank you for your order!", f"Unexpected completion message: '{message}'"
    _pause()
    menu_button = context.wait.until(EC.element_to_be_clickable((By.ID, "react-burger-menu-btn")))
    menu_button.click()
    _pause()
    logout_link = context.wait.until(EC.element_to_be_clickable((By.ID, "logout_sidebar_link")))
    logout_link.click()
    context.wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
    _pause()


@when('the user sorts the inventory by "{order_text}"')
def step_sort_inventory(context, order_text: str):
    sorter = context.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "product_sort_container")))
    Select(sorter).select_by_visible_text(order_text)
    _pause()


@then('the first inventory item should display price "{price}"')
def step_verify_first_price(context, price: str):
    context.wait.until(lambda _: context.driver.find_elements(By.CLASS_NAME, "inventory_item_price"))
    prices = context.driver.find_elements(By.CLASS_NAME, "inventory_item_price")
    assert prices, "No inventory prices found after sorting"
    first_price = prices[0].text.strip()
    assert first_price == price, f"Expected first price {price} but saw '{first_price}'"
    _pause()


@then('the inventory should list "{item_name}" first')
def step_verify_first_item_name(context, item_name: str):
    context.wait.until(lambda _: context.driver.find_elements(By.CLASS_NAME, "inventory_item_name"))
    names = context.driver.find_elements(By.CLASS_NAME, "inventory_item_name")
    assert names, "No inventory names found after sorting"
    first_name = names[0].text.strip()
    assert (
        first_name == item_name
    ), f"Expected first inventory item '{item_name}' but saw '{first_name}'"
    _pause()


def _add_item_to_cart(context, item_name: str) -> None:
    button_id = ITEM_ADD_BUTTONS.get(item_name)
    if not button_id:
        raise AssertionError(f"No add-to-cart mapping defined for item '{item_name}'")
    context.wait.until(EC.element_to_be_clickable((By.ID, button_id))).click()
    remove_xpath = (
        f"//div[@class='inventory_item'][.//div[text()=\"{item_name}\"]]//button[normalize-space()='Remove']"
    )
    context.wait.until(EC.presence_of_element_located((By.XPATH, remove_xpath)))


def _remove_item_from_cart(context, item_name: str) -> None:
    remove_id = REMOVE_BUTTON_IDS.get(item_name)
    if not remove_id:
        raise AssertionError(f"No remove mapping defined for item '{item_name}'")
    add_id = ITEM_ADD_BUTTONS.get(item_name)
    if not add_id:
        raise AssertionError(f"No add-to-cart mapping defined for item '{item_name}'")
    context.wait.until(EC.element_to_be_clickable((By.ID, remove_id))).click()
    context.wait.until(EC.element_to_be_clickable((By.ID, add_id)))


def _wait_for_cart_badge(context, expected_text: str) -> None:
    context.wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, "shopping_cart_badge"), expected_text))


def _pause(seconds: float | None = None) -> None:
    sleep_for = seconds if seconds is not None else DEFAULT_PAUSE
    if sleep_for > 0:
        time.sleep(sleep_for)


def _build_driver():
    remote_executor, remote_label = _resolve_remote_executor()
    browser = os.getenv("BROWSER", "firefox").strip().lower()

    if remote_label == "healenium":
        print(f"[driver] Routing WebDriver session through Healenium proxy at {remote_executor}")
    elif remote_label == "grid":
        print(f"[driver] Using remote WebDriver endpoint {remote_executor}")

    if browser == "firefox":
        firefox_options = FirefoxOptions()
        firefox_options.set_preference("signon.rememberSignons", False)
        firefox_options.set_preference("signon.autofillForms", False)
        firefox_options.set_preference("signon.autofillForms.http", False)
        firefox_options.set_preference("signon.storeWhenAutocompleteOff", False)
        firefox_options.set_preference("dom.webnotifications.enabled", False)
        firefox_options.set_preference("browser.sessionstore.warnOnQuit", False)
        firefox_options.add_argument("-width=1920")
        firefox_options.add_argument("-height=1080")
        if remote_executor:
            return webdriver.Remote(command_executor=remote_executor, options=firefox_options)
        return webdriver.Firefox(options=firefox_options)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-save-password-bubble")
    chrome_options.add_argument("--disable-features=PasswordManagerOnboarding,PasswordLeakDetection")
    chrome_options.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        },
    )
    chrome_options.add_argument("--disable-notifications")
    if remote_executor:
        return webdriver.Remote(command_executor=remote_executor, options=chrome_options)
    return webdriver.Chrome(options=chrome_options)


def _dismiss_password_security_alert(driver) -> None:
    try:
        WebDriverWait(driver, 3).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
    except (TimeoutException, NoAlertPresentException):
        pass


def _resolve_remote_executor() -> Tuple[str | None, str]:
    """Determine if the driver should talk to Grid or a Healenium proxy."""

    def _truthy(value: str | None) -> bool:
        return bool(value and value.strip().lower() in {"1", "true", "yes", "on"})

    healenium_url = os.getenv("HEALENIUM_URL") or os.getenv("HEALENIUM_PROXY_URL")
    use_healenium = _truthy(os.getenv("USE_HEALENIUM"))
    grid_url = os.getenv("GRID_URL")

    if healenium_url:
        return healenium_url.rstrip("/"), "healenium"
    if use_healenium and grid_url:
        return grid_url.rstrip("/"), "healenium"
    if grid_url:
        return grid_url.rstrip("/"), "grid"
    return None, "local"
