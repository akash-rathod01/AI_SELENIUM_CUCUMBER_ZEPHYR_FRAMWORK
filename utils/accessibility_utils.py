# utils/accessibility_utils.py
from selenium.webdriver.remote.webdriver import WebDriver
from loguru import logger
import time

class AccessibilityUtils:
    @staticmethod
    def run_axe(driver: WebDriver):
        # Inject axe-core script
        axe_url = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.2/axe.min.js"
        driver.execute_script(f"var s=document.createElement('script');s.src='{axe_url}';document.head.appendChild(s);")
        time.sleep(2)  # Wait for script to load
        # Run axe
        result = driver.execute_script("return axe.run();")
        logger.info(f"Accessibility violations: {result['violations']}")
        return result['violations']
