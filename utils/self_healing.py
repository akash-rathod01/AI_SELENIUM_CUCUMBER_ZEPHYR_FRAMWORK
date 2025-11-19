
from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

try:
	from loguru import logger  # type: ignore
except ImportError:  # pragma: no cover
	import logging

	logging.basicConfig(level=logging.INFO)
	logger = logging.getLogger(__name__)
from selenium.common.exceptions import NoSuchElementException, WebDriverException


class SelfHealingLocator:
	"""Attempts alternate locator strategies and records telemetry for future runs."""

	def __init__(
		self,
		driver,
		strategies=None,
		screenshot_dir: str = "failed_tests",
		telemetry_path: str = "self_healing_metrics.json",
	):
		self.driver = driver
		self.strategies = strategies or ['xpath', 'css selector', 'id', 'name', 'class name']
		self.screenshot_dir = screenshot_dir
		self.telemetry_path = Path(telemetry_path)
		self.telemetry: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
		self._load_telemetry()
		if not os.path.exists(self.screenshot_dir):
			os.makedirs(self.screenshot_dir)

	def find_element(self, locator_type, locator_value, test_name: Optional[str] = None):
		try:
			element = self.driver.find_element(locator_type, locator_value)
			self._record_event(locator_type, locator_value, "success", locator_type)
			return element
		except NoSuchElementException:
			logger.warning(
				f"Element not found: {locator_type}={locator_value}. Trying self-healing strategies."
			)
			self._record_event(locator_type, locator_value, "failure", locator_type)
			return self._attempt_healing(locator_type, locator_value, test_name)

	def _attempt_healing(self, locator_type: str, locator_value: str, test_name: Optional[str]):
		for strategy in self.strategies:
			if strategy == locator_type:
				continue
			try:
				element = self.driver.find_element(strategy, locator_value)
				logger.info(f"Element recovered using {strategy}={locator_value}")
				self._record_event(locator_type, locator_value, "healed", strategy)
				self._persist_suggestion(locator_type, locator_value, strategy)
				return element
			except NoSuchElementException:
				self._record_event(locator_type, locator_value, "attempt", strategy)
				continue

		logger.error(f"Element not found with any strategy: {locator_value}")
		if test_name:
			self.save_screenshot(test_name)
		raise NoSuchElementException(locator_value)

	def _persist_suggestion(self, locator_type: str, locator_value: str, strategy: str) -> None:
		self.telemetry[locator_value]["suggested_strategy"] = strategy
		self._save_telemetry()

	def save_screenshot(self, test_name: str) -> None:
		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
		filename = f"{test_name}_failed_{timestamp}.png"
		filepath = os.path.join(self.screenshot_dir, filename)
		try:
			self.driver.save_screenshot(filepath)
			logger.info(f"Screenshot saved: {filepath}")
		except WebDriverException as exc:  # pragma: no cover - best effort
			logger.error(f"Failed to save screenshot: {exc}")

	def update_locator(self, old_locator, new_locator) -> None:
		logger.info(f"Updating locator from {old_locator} to {new_locator}")
		self.telemetry[str(old_locator)]["last_update"] = datetime.utcnow().isoformat()
		self.telemetry[str(old_locator)]["new_locator"] = str(new_locator)
		self._save_telemetry()

	def _record_event(self, locator_type: str, locator_value: str, status: str, strategy: str) -> None:
		key = f"{locator_type}:{locator_value}"
		self.telemetry[key][status] = self.telemetry[key].get(status, 0) + 1
		self.telemetry[key]["last_strategy"] = strategy
		self._save_telemetry()

	def _load_telemetry(self) -> None:
		if self.telemetry_path.exists():
			with self.telemetry_path.open("r", encoding="utf-8") as handle:
				data = json.load(handle)
				self.telemetry.update(data)

	def _save_telemetry(self) -> None:
		with self.telemetry_path.open("w", encoding="utf-8") as handle:
			json.dump(self.telemetry, handle, indent=2)

	def extract_dom_signature(self, element) -> Dict[str, str]:
		"""Capture element attributes to aid future healing suggestions."""
		try:
			return self.driver.execute_script(
				"""
				var attrs = arguments[0].attributes;
				var result = {};
				for (var i = 0; i < attrs.length; i++) {
					result[attrs[i].name] = attrs[i].value;
				}
				return result;
				""",
				element,
			)
		except WebDriverException:
			return {}

