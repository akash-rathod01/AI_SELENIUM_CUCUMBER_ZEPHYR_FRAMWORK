from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException

from pages.base_page import BasePage


class LoginPage(BasePage):
    USERNAME_INPUT = (By.CSS_SELECTOR, 'input.gwt-TextBox.GDPVGE1BC3B')
    PASSWORD_INPUT = (By.CSS_SELECTOR, 'input.gwt-PasswordTextBox.GDPVGE1BC3B')
    SIGNIN_BUTTON = (By.CSS_SELECTOR, 'button[data-automation-id="goButton"]')
    REMEMBER_DEVICE_SKIP = (By.XPATH, "//a[contains(text(), 'Skip')]")

    def login(self, username, password):
        self.enter_text(*self.USERNAME_INPUT, text=username)
        self.enter_text(*self.PASSWORD_INPUT, text=password)
        wait = WebDriverWait(self.driver, 20)
        wait.until(EC.element_to_be_clickable(self.SIGNIN_BUTTON))
        try:
            self.click(*self.SIGNIN_BUTTON)
        except WebDriverException:
            # Fallback for overlays intercepting the click
            self.driver.execute_script("arguments[0].click();", self.find(*self.SIGNIN_BUTTON))

    def skip_remember_device(self):
        wait = WebDriverWait(self.driver, 30)
        self.driver.save_screenshot('before_skip.png')
        if self._try_click_skip(wait):
            return

        # Attempt within iframes if the prompt is embedded
        frames = self.driver.find_elements(By.TAG_NAME, "iframe")
        for frame in frames:
            self.driver.switch_to.frame(frame)
            try:
                if self._try_click_skip(wait):
                    return
            finally:
                self.driver.switch_to.default_content()

        raise TimeoutException("Unable to locate the Remember Device 'Skip' control after login")

    def _try_click_skip(self, wait: WebDriverWait) -> bool:
        try:
            skip_element = wait.until(EC.element_to_be_clickable(self.REMEMBER_DEVICE_SKIP))
        except TimeoutException:
            return False

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", skip_element)
        try:
            skip_element.click()
        except WebDriverException:
            self.driver.execute_script("arguments[0].click();", skip_element)
        return True
