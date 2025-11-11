
from loguru import logger
from selenium.common.exceptions import NoSuchElementException


import os
from datetime import datetime

class SelfHealingLocator:
	def __init__(self, driver, strategies=None, screenshot_dir='failed_tests'):
		self.driver = driver
		self.strategies = strategies or ['xpath', 'css selector', 'id', 'name', 'class name']
		self.screenshot_dir = screenshot_dir
		if not os.path.exists(self.screenshot_dir):
			os.makedirs(self.screenshot_dir)


	def find_element(self, locator_type, locator_value, test_name=None):
		try:
			return self.driver.find_element(locator_type, locator_value)
		except NoSuchElementException:
			logger.warning(f"Element not found: {locator_type}={locator_value}. Trying self-healing strategies.")
			for strategy in self.strategies:
				if strategy == locator_type:
					continue
				try:
					element = self.driver.find_element(strategy, locator_value)
					logger.info(f"Element found using {strategy}={locator_value}")
					return element
				except NoSuchElementException:
					continue
			logger.error(f"Element not found with any strategy: {locator_value}")
			if test_name:
				self.save_screenshot(test_name)
			raise

	def save_screenshot(self, test_name):
		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
		filename = f"{test_name}_failed_{timestamp}.png"
		filepath = os.path.join(self.screenshot_dir, filename)
		self.driver.save_screenshot(filepath)
	logger.info(f"Screenshot saved: {filepath}")


	def update_locator(self, old_locator, new_locator):
		# Placeholder for logic to update locator in test scripts or config
		logger.info(f"Updating locator from {old_locator} to {new_locator}")
		# Implement persistence logic as needed
		pass

# Example usage:
# from selenium import webdriver
# driver = webdriver.Chrome()
# healer = SelfHealingLocator(driver)
# element = healer.find_element('xpath', '//button[@id="submit"]')
