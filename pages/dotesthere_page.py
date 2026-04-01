"""Page objects and reusable helpers for dotesthere.com automation."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple

import requests

from selenium.common.exceptions import (
	ElementNotInteractableException,
	InvalidElementStateException,
	MoveTargetOutOfBoundsException,
	NoAlertPresentException,
	NoSuchElementException,
	StaleElementReferenceException,
	TimeoutException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait


class DoTestHerePage:
		def _auto_heal_action(self, action_fn, locator, max_retries=3, alt_locators=None, action_desc=""):
			"""Auto-healing wrapper for element actions. Tries main and alternative locators, retries on failure, logs errors."""
			last_exception = None
			locators_to_try = [locator] + (alt_locators or [])
			for attempt in range(max_retries):
				for loc in locators_to_try:
					try:
						return action_fn(loc)
					except Exception as e:
						last_exception = e
			print(f"[AUTO-HEAL] Failed to {action_desc or action_fn.__name__} after {max_retries} retries. Last error: {last_exception}")
			raise last_exception
	"""Unified page object exposing rich interactions for dotesthere.com."""

	HOME_URL = "https://dotesthere.com/"

	MODULE_SELECTORS: Dict[str, Tuple[str, str]] = {
		"ab-testing": ("#ab-testing", 'div.element-card[data-element="ab-testing"]'),
		"add-remove": ("#add-remove", 'div.element-card[data-element="add-remove"]'),
		"basic-auth": ("#basic-auth", 'div.element-card[data-element="basic-auth"]'),
		"broken-images": ("#broken-images", 'div.element-card[data-element="broken-images"]'),
		"challenging-dom": ("#challenging-dom", 'div.element-card[data-element="challenging-dom"]'),
		"checkboxes": ("#checkboxes", 'div.element-card[data-element="checkboxes"]'),
		"context-menu": ("#context-menu", 'div.element-card[data-element="context-menu"]'),
		"disappearing": ("#disappearing", 'div.element-card[data-element="disappearing"]'),
		"drag-drop": ("#drag-drop", 'div.element-card[data-element="drag-drop"]'),
		"dropdown": ("#dropdown", 'div.element-card[data-element="dropdown"]'),
		"dynamic-content": ("#dynamic-content", 'div.element-card[data-element="dynamic-content"]'),
		"dynamic-controls": ("#dynamic-controls", 'div.element-card[data-element="dynamic-controls"]'),
		"dynamic-loading": ("#dynamic-loading", 'div.element-card[data-element="dynamic-loading"]'),
		"file-download": ("#file-download", 'div.element-card[data-element="file-download"]'),
		"file-upload": ("#file-upload", 'div.element-card[data-element="file-upload"]'),
		"form-auth": ("#form-auth", 'div.element-card[data-element="form-auth"]'),
		"frames": ("#frames", 'div.element-card[data-element="frames"]'),
		"horizontal-slider": ("#horizontal-slider", 'div.element-card[data-element="horizontal-slider"]'),
		"hovers": ("#hovers", 'div.element-card[data-element="hovers"]'),
		"javascript-alerts": ("#js-alerts", 'div.element-card[data-element="javascript-alerts"]'),
		"key-presses": ("#key-presses", 'div.element-card[data-element="key-presses"]'),
		"multiple-windows": ("#multiple-windows", 'div.element-card[data-element="multiple-windows"]'),
		"shadow-dom": ("#shadow-dom", 'div.element-card[data-element="shadow-dom"]'),
		"sortable-tables": ("#sortable-tables", 'div.element-card[data-element="sortable-tables"]'),
		"wysiwyg": ("#wysiwyg", 'div.element-card[data-element="wysiwyg"]'),
	}

	def __init__(self, driver, wait: WebDriverWait | None = None, default_timeout: int = 15) -> None:
		self.driver = driver
		self.wait = wait or WebDriverWait(driver, default_timeout)

	def _get_module_card(self, module_key: str):
		"""Return the module card element, waiting for it to exist."""

		_, card_selector = self.MODULE_SELECTORS.get(
			module_key,
			(f"#{module_key}", f'div.element-card[data-element="{module_key}"]'),
		)
		return self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, card_selector)))

	def navigate_to_home(self) -> None:
		"""Open the home page if we are not already there."""

		current = self.driver.current_url or ""
		if not current.startswith(self.HOME_URL):
			self.driver.get(self.HOME_URL)
		self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "aside nav")))

	def get_page_title(self) -> str:
		return (self.driver.title or "").strip()

	def visit_and_verify(
		self,
		url: str,
		title_expectations: str | List[str] | Tuple[str, ...],
		*,
		check_status: bool = True,
	) -> str:
		"""Navigate to ``url`` and ensure the rendered title matches expectations."""

		if check_status:
			try:
				resp = requests.get(url, timeout=10)
				resp.raise_for_status()
			except requests.RequestException as exc:  # pragma: no cover - network edge cases
				raise AssertionError(f"HTTP status check failed for {url}: {exc}") from exc

		self.driver.get(url)
		self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

		title = self.get_page_title()
		expectations: List[str]
		if isinstance(title_expectations, str):
			expectations = [title_expectations]
		else:
			expectations = list(title_expectations)

		if expectations and not any(exp.lower() in title.lower() for exp in expectations):
			raise AssertionError(f"Title '{title}' did not contain any of {expectations}")
		return title

	def open_module(self, module_key: str) -> None:
		"""Scroll to a module tile using the left navigation."""

		anchor, card_selector = self.MODULE_SELECTORS.get(
			module_key,
			(f"#{module_key}", f'div.element-card[data-element="{module_key}"]'),
		)
		nav_selector = f"aside nav a[href='{anchor}']"
		try:
			link = self.wait.until(
				EC.presence_of_element_located((By.CSS_SELECTOR, nav_selector))
			)
			self.driver.execute_script(
				"arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
				link,
			)
			self.driver.execute_script("arguments[0].click();", link)
		except TimeoutException:
			# Navigation anchor missing or not interactive; rely on card lookup directly.
			pass

		try:
			card = self._get_module_card(module_key)
			self.driver.execute_script(
				"arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
				card,
			)
			self.wait.until(lambda _driver: card.is_displayed())
		except TimeoutException:
			pass

		time.sleep(0.2)

	def is_module_visible(self, module_key: str) -> bool:
		"""Return True when the requested module tile is visible on the page."""

		_, card_selector = self.MODULE_SELECTORS.get(
			module_key,
			(f"#{module_key}", f'div.element-card[data-element="{module_key}"]'),
		)
		try:
			card = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, card_selector)))
			return card.is_displayed()
		except TimeoutException:
			return False

	def get_primary_navigation_links(self) -> List[Tuple[str, str]]:
		links: List[Tuple[str, str]] = []
		for link in self.driver.find_elements(By.CSS_SELECTOR, "aside nav a"):
			text = link.text.strip()
			href = link.get_attribute("href") or link.get_attribute("data-href")
			links.append((text, href or ""))
		return links

	# ------------------------------------------------------------------
	# Manual testing lab helpers
	# ------------------------------------------------------------------
	def manual_lab_fill_fields(self, field_values: Dict[str, str]) -> None:
		def fill_fn(locators):
			locator, value = locators
			if locator.startswith("//"): 
				element = self.wait.until(EC.presence_of_element_located((By.XPATH, locator)))
			else:
				try:
					element = self.wait.until(EC.presence_of_element_located((By.ID, locator)))
				except TimeoutException:
					element = self.wait.until(EC.presence_of_element_located((By.NAME, locator)))
			self.driver.execute_script(
				"arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
				element,
			)
			try:
				ActionChains(self.driver).move_to_element(element).pause(0.05).perform()
			except (ElementNotInteractableException, MoveTargetOutOfBoundsException):
				pass
			self.wait.until(lambda _driver: element.is_enabled())
			if element.tag_name.lower() == "select":
				select = Select(element)
				lower_value = value.strip().lower()
				matched_option = None
				for option in select.options:
					text = (option.text or "").strip()
					if text.lower() == lower_value:
						matched_option = option
						break
				if not matched_option:
					for option in select.options:
						text = (option.text or "").strip()
						if lower_value and lower_value in text.lower():
							matched_option = option
							break
				if not matched_option:
					for option in select.options:
						opt_value = (option.get_attribute("value") or "").strip()
						if opt_value.lower() == lower_value:
							matched_option = option
							break
				if matched_option:
					option_text = (matched_option.text or "").strip()
					option_value = (matched_option.get_attribute("value") or "").strip()
					try:
						if option_text:
							select.select_by_visible_text(option_text)
						elif option_value:
							select.select_by_value(option_value)
						else:
							matched_option.click()
					except NoSuchElementException:
						if option_value:
							select.select_by_value(option_value)
						else:
							self.driver.execute_script("arguments[0].selected = true;", matched_option)
							self.driver.execute_script(
								"arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
								element,
							)
				elif len(select.options) > 1:
					select.select_by_index(1)
				else:
					select.select_by_index(0)
				self.driver.execute_script(
					"arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
					element,
				)
				return True
			input_type = (element.get_attribute("type") or "").lower()
			if input_type == "range":
				self.driver.execute_script(
					"arguments[0].value = arguments[1];"
					"arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
					"arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
					element,
					str(value),
				)
				return True
			if input_type in {"checkbox", "radio"}:
				should_select = str(value).lower() in {"1", "true", "yes", "on", "checked"}
				if element.is_selected() != should_select:
					self.driver.execute_script("arguments[0].click();", element)
				return True
			try:
				element.clear()
			except (
				ElementNotInteractableException,
				StaleElementReferenceException,
				InvalidElementStateException,
			):
				self.driver.execute_script("arguments[0].value='';", element)
			try:
				element.send_keys(value)
			except ElementNotInteractableException:
				self.driver.execute_script("arguments[0].value = arguments[1];", element, value)
			return True
		for locator, value in field_values.items():
			alt_locators = []
			if not locator.startswith("//"):
				alt_locators.append((By.NAME, locator))
			self._auto_heal_action(lambda loc: fill_fn((locator, value)), (By.XPATH, locator) if locator.startswith("//") else (By.ID, locator), alt_locators=alt_locators, action_desc=f"fill field '{locator}'")

	def manual_lab_click(self, locator: Tuple[str, str]) -> None:
		try:
			element = self.wait.until(EC.element_to_be_clickable(locator))
		except TimeoutException:
			self.wait.until(EC.presence_of_element_located(locator))
			self.wait.until(lambda _driver: self.driver.find_element(*locator).is_displayed())
			element = self.driver.find_element(*locator)
		self.driver.execute_script(
			"arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
			element,
		)
		self.driver.execute_script("arguments[0].click();", element)

	def manual_lab_block_text(self, element_id: str) -> str:
		block = self.wait.until(EC.visibility_of_element_located((By.ID, element_id)))
		return block.text.strip()

	# ------------------------------------------------------------------
	# A/B test and element playground helpers
	# ------------------------------------------------------------------
	def switch_ab_test_version(self) -> str:
		btn = self.wait.until(
			EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Switch Version')]")
			)
		)
		self.driver.execute_script("arguments[0].click();", btn)
		heading = self.wait.until(EC.visibility_of_element_located((By.ID, "ab-heading")))
		return heading.text.strip()

	def add_element(self) -> None:
		btn = self.wait.until(
			EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Add Element')]")
			)
		)
		self.driver.execute_script("arguments[0].click();", btn)

	def count_delete_buttons(self) -> int:
		return len(self.driver.find_elements(By.CSS_SELECTOR, "#elements-container .delete-btn"))

	def delete_first_element(self) -> None:
		locator = (By.CSS_SELECTOR, "#elements-container .delete-btn")
		buttons = self.driver.find_elements(*locator)
		if buttons:
			initial = len(buttons)
			self.driver.execute_script("arguments[0].click();", buttons[0])
			try:
				self.wait.until(lambda _driver: len(_driver.find_elements(*locator)) < initial)
			except TimeoutException:
				pass

	def trigger_basic_auth(self) -> str:
		card = self._get_module_card("basic-auth")
		buttons = card.find_elements(By.TAG_NAME, "button") or card.find_elements(
			By.CSS_SELECTOR, "a, input[type='button']"
		)
		btn = None
		for candidate in buttons:
			text = (candidate.text or "").strip().lower()
			if "test basic auth" in text or "authenticate" in text:
				btn = candidate
				break
		if btn is None:
			raise AssertionError("Basic Auth control not found")
		self.driver.execute_script(
			"arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
			btn,
		)
		self.driver.execute_script("arguments[0].click();", btn)
		result = self.wait.until(EC.presence_of_element_located((By.ID, "auth-result")))
		self.wait.until(lambda _driver: bool(result.text.strip()))
		return result.text.strip()

	def identify_broken_images(self) -> Tuple[int, int]:
		images = self.driver.find_elements(By.CSS_SELECTOR, "div[data-element='broken-images'] img")
		broken = sum(1 for img in images if img.get_attribute("naturalWidth") == "0")
		return len(images), broken

	def click_challenging_table_action(self, action: str) -> None:
		main_locator = (
			By.XPATH,
			"//table//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), "
			f"'{action.lower()}')]",
		)
		alt_locator = (
			By.XPATH,
			f"//table//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{action.lower()}')]"
		)
		def click_fn(locator):
			try:
				button = self.wait.until(EC.element_to_be_clickable(locator))
			except TimeoutException:
				button = self.wait.until(EC.presence_of_element_located(locator))
			self.driver.execute_script(
				"arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
				button,
			)
			self.driver.execute_script("arguments[0].click();", button)
			return True
		self._auto_heal_action(click_fn, main_locator, alt_locators=[alt_locator], action_desc=f"click '{action}' table button")

	def toggle_checkbox(self, checkbox_id: str) -> bool:
		locator = (By.ID, checkbox_id)
		checkbox = self.wait.until(EC.presence_of_element_located(locator))
		self.driver.execute_script(
			"arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
			checkbox,
		)
		initial = checkbox.is_selected()
		self.wait.until(EC.element_to_be_clickable(locator))
		checkbox.click()
		self.wait.until(lambda _driver: self.driver.find_element(*locator).is_selected() != initial)
		return self.driver.find_element(*locator).is_selected()

	def right_click_hotspot(self) -> str | None:
		hotspot = self.wait.until(EC.presence_of_element_located((By.ID, "hot-spot")))
		ActionChains(self.driver).context_click(hotspot).perform()
		time.sleep(0.2)
		try:
			alert = self.driver.switch_to.alert
			message = alert.text
			alert.accept()
			return message
		except NoAlertPresentException:
			return None

	def drag_column_a_to_b(self) -> str:
		col_a = self.wait.until(EC.presence_of_element_located((By.ID, "column-a")))
		col_b = self.wait.until(EC.presence_of_element_located((By.ID, "column-b")))
		ActionChains(self.driver).drag_and_drop(col_a, col_b).perform()
		status = self.wait.until(EC.visibility_of_element_located((By.ID, "drag-status")))
		return status.text.strip()

	def select_dropdown_option(self, option_text: str) -> None:
		dropdown = self.wait.until(EC.element_to_be_clickable((By.ID, "dropdown")))
		Select(dropdown).select_by_visible_text(option_text)

	def get_selected_dropdown_option(self) -> str:
		dropdown = self.driver.find_element(By.ID, "dropdown")
		return Select(dropdown).first_selected_option.text.strip()

	def refresh_dynamic_content(self) -> str:
		area_locator = (By.ID, "dynamic-content-area")
		area = self.wait.until(EC.visibility_of_element_located(area_locator))
		previous = area.text.strip()
		btn = self.wait.until(
			EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Refresh Content')]")
			)
		)
		self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
		self.driver.execute_script("arguments[0].click();", btn)
		self.wait.until(
			lambda _driver: self.driver.find_element(*area_locator).text.strip() != previous
		)
		return self.driver.find_element(*area_locator).text.strip()

	def is_dynamic_checkbox_present(self) -> bool:
		try:
			checkbox = self.driver.find_element(By.ID, "dynamic-checkbox")
		except NoSuchElementException:
			return False
		return checkbox.is_displayed()

	def toggle_dynamic_checkbox(self) -> bool:
		card = self._get_module_card("dynamic-controls")
		btn = card.find_element(
			By.XPATH,
			".//div[contains(@class,'control-group')][1]//button",
		)
		self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
		initial = self.is_dynamic_checkbox_present()
		self.driver.execute_script("arguments[0].click();", btn)
		self.wait.until(lambda _driver: self.is_dynamic_checkbox_present() != initial)
		return self.is_dynamic_checkbox_present()

	def is_dynamic_input_enabled(self) -> bool:
		try:
			field = self.wait.until(EC.presence_of_element_located((By.ID, "dynamic-input")))
		except TimeoutException:
			return False
		return field.is_enabled()

	def toggle_dynamic_input(self) -> bool:
		card = self._get_module_card("dynamic-controls")
		btn = card.find_element(
			By.XPATH,
			".//div[contains(@class,'control-group')][2]//button",
		)
		self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
		initial = self.is_dynamic_input_enabled()
		self.driver.execute_script("arguments[0].click();", btn)
		self.wait.until(lambda _driver: self.is_dynamic_input_enabled() != initial)
		return self.is_dynamic_input_enabled()

	def start_loading(self) -> str:
		btn = self.wait.until(
			EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Start')]")
			)
		)
		self.driver.execute_script("arguments[0].click();", btn)
		self.wait.until(EC.visibility_of_element_located((By.ID, "loading-spinner")))
		self.wait.until(EC.invisibility_of_element_located((By.ID, "loading-spinner")))
		finish = self.wait.until(EC.visibility_of_element_located((By.ID, "finish-text")))
		return finish.text.strip()

	def hover_on_figure(self, figure_index: int) -> str:
		figures = self.driver.find_elements(By.CSS_SELECTOR, ".figure")
		if 0 <= figure_index < len(figures):
			ActionChains(self.driver).move_to_element(figures[figure_index]).perform()
			caption = figures[figure_index].find_element(By.CLASS_NAME, "figcaption")
			return caption.text.strip()
		return ""

	def click_js_alert(self) -> str | None:
		btn = self.wait.until(
			EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'JS Alert')]")
			)
		)
		self.driver.execute_script("arguments[0].click();", btn)
		try:
			alert = self.driver.switch_to.alert
			message = alert.text
			alert.accept()
			return message
		except NoAlertPresentException:
			return None

	def click_js_confirm(self, accept: bool = True) -> str | None:
		btn = self.wait.until(
			EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'JS Confirm')]")
			)
		)
		self.driver.execute_script("arguments[0].click();", btn)
		try:
			alert = self.driver.switch_to.alert
			message = alert.text
			if accept:
				alert.accept()
			else:
				alert.dismiss()
			return message
		except NoAlertPresentException:
			return None

	def click_js_prompt(self, text_to_enter: str) -> str | None:
		btn = self.wait.until(
			EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'JS Prompt')]")
			)
		)
		self.driver.execute_script("arguments[0].click();", btn)
		try:
			alert = self.driver.switch_to.alert
			message = alert.text
			alert.send_keys(text_to_enter)
			alert.accept()
			return message
		except NoAlertPresentException:
			return None

	def enter_key_press(self, key: Any) -> str:
		field = self.wait.until(EC.element_to_be_clickable((By.ID, "target")))
		field.click()
		field.send_keys(key)
		result = self.wait.until(EC.visibility_of_element_located((By.ID, "key-result")))
		return result.text.strip()

	def click_new_window(self) -> int:
		card = self._get_module_card("multiple-windows")
		link = None
		for candidate in card.find_elements(By.CSS_SELECTOR, "a, button"):
			text = (candidate.text or "").strip().lower()
			if "click here" in text:
				link = candidate
				break
		if link is None:
			raise AssertionError("Multiple Windows trigger not found")
		self.driver.execute_script(
			"arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
			link,
		)
		initial_handles = len(self.driver.window_handles)
		self.driver.execute_script("arguments[0].click();", link)
		self.wait.until(lambda driver: len(driver.window_handles) > initial_handles)
		return len(self.driver.window_handles)

	def get_shadow_dom_text(self) -> str:
		try:
			host = self.driver.find_element(By.ID, "shadow-host")
			text_el = host.shadow_root.find_element(By.CSS_SELECTOR, "p")
			return text_el.text.strip()
		except Exception:
			return ""

	def click_table_header(self, header_text: str) -> None:
		card = self._get_module_card("sortable-tables")
		headers = self.wait.until(
			lambda _driver: card.find_elements(By.CSS_SELECTOR, "table thead th") or False
		)
		target = None
		needle = header_text.strip().lower()
		for candidate in headers:
			if (candidate.text or "").strip().lower() == needle:
				target = candidate
				break
		if target is None:
			raise AssertionError(f"Sortable table header '{header_text}' not found")
		self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
		self.driver.execute_script("arguments[0].click();", target)

	def get_first_table_row_cells(self) -> List[str]:
		card = self._get_module_card("sortable-tables")
		self.wait.until(lambda _driver: card.find_elements(By.CSS_SELECTOR, "table tbody tr"))
		rows = card.find_elements(By.CSS_SELECTOR, "table tbody tr")
		if not rows:
			return []
		cells = rows[0].find_elements(By.TAG_NAME, "td")
		return [cell.text.strip() for cell in cells]

	def enter_wysiwyg_text(self, text: str) -> None:
		editor = self.wait.until(EC.presence_of_element_located((By.ID, "editor")))
		self.driver.execute_script("arguments[0].focus();", editor)
		self.driver.execute_script("arguments[0].innerHTML='';", editor)
		editor.send_keys(text)

	def get_wysiwyg_text(self) -> str:
		editor = self.wait.until(EC.presence_of_element_located((By.ID, "editor")))
		return editor.text.strip()

