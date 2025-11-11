from loguru import logger

"""
BasePage: Abstracts common Selenium actions for maintainable Page Object Model.
All page classes should inherit from BasePage.
"""

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class BasePage:
	def __init__(self, driver, timeout=10):
		self.driver = driver
		self.timeout = timeout

	def find(self, by, value):
		return self.driver.find_element(by, value)

	def find_and_wait(self, by, value):
		try:
			return WebDriverWait(self.driver, self.timeout).until(
				EC.presence_of_element_located((by, value))
			)
		except TimeoutException:
			return None

	def click(self, by, value):
		element = self.find_and_wait(by, value)
		if element:
			logger.info(f"Clicking element: {by}={value}")
			element.click()
		else:
			logger.error(f"Element not found: {by}={value}")
			raise Exception(f"Element not found: {by}={value}")

	def enter_text(self, by, value, text):
		element = self.find_and_wait(by, value)
		if element:
			logger.info(f"Entering text in element: {by}={value}")
			element.clear()
			element.send_keys(text)
		else:
			logger.error(f"Element not found: {by}={value}")
			raise Exception(f"Element not found: {by}={value}")

	def get_title(self):
		return self.driver.title
