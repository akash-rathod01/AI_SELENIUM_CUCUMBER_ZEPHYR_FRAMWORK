"""Generate draft Gherkin scenarios from natural language requirements."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional

try:
	from loguru import logger
except ImportError:  # pragma: no cover - fallback when loguru missing
	class _FallbackLogger:
		def __getattr__(self, name):
			def _noop(*args, **kwargs):  # noqa: D401 - simple fallback
				"""No-op logger method."""

			return _noop

	logger = _FallbackLogger()

try:
	import openai  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
	openai = None

from config.ai_settings import load_settings


_DEFAULT_PROMPT = (
	"Convert the requirement below into Behave (Gherkin) scenarios. "
	"Return JSON with a 'scenarios' array; each item must contain 'title' and 'steps'."
)


@dataclass
class GeneratedScenario:
	title: str
	steps: List[str]

	def to_gherkin(self) -> str:
		lines = [f"  Scenario: {self.title}"]
		for step in self.steps:
			lines.append(f"    {step}")
		return "\n".join(lines)


class NLPTestGenerator:
	"""Transforms product requirements into Gherkin drafts."""

	def __init__(self, prompt: str = _DEFAULT_PROMPT):
		self.prompt = prompt
		self.settings = load_settings()

	def generate(self, requirement: str, use_llm: Optional[bool] = None) -> List[GeneratedScenario]:
		"""Generate test scenarios using an LLM (if configured) with rule-based fallback."""

		if use_llm is None:
			use_llm = self.settings.enable_nlp and bool(self.settings.api_key) and openai is not None

		if use_llm:
			try:
				scenarios = self._generate_with_llm(requirement)
				logger.info(f"Generated scenarios via LLM for requirement: {requirement}")
				return scenarios
			except Exception as exc:  # pragma: no cover - network failure path
				logger.warning(f"LLM generation failed; using heuristic fallback. Error: {exc}")

		return self._heuristic_generation(requirement)

	# region LLM
	def _generate_with_llm(self, requirement: str) -> List[GeneratedScenario]:
		if openai is None:
			raise RuntimeError("openai package not installed")
		self.settings.validate()
		openai.api_key = self.settings.api_key
		if self.settings.api_base:
			openai.api_base = self.settings.api_base

		response = openai.ChatCompletion.create(  # type: ignore[attr-defined]
			model="gpt-4o-mini",
			messages=[
				{"role": "system", "content": "You are a senior QA engineer."},
				{"role": "user", "content": f"{self.prompt}\n\nRequirement:\n{requirement}"},
			],
			max_tokens=self.settings.max_tokens,
			temperature=0.2,
			timeout=self.settings.request_timeout,
		)

		content = response["choices"][0]["message"]["content"]
		parsed = json.loads(content)
		return [GeneratedScenario(**item) for item in parsed["scenarios"]]

	# endregion

	# region heuristic fallback
	def _heuristic_generation(self, requirement: str) -> List[GeneratedScenario]:
		sentences = _split_sentences(requirement)
		if not sentences:
			logger.warning("No requirement sentences detected; returning empty scenarios")
			return []

		scenarios: List[GeneratedScenario] = []
		for idx, sentence in enumerate(sentences, start=1):
			steps = ["Given the application is prepared"]
			if "login" in sentence.lower():
				steps.extend(
					[
						"When the user enters valid credentials",
						"Then the user should be logged in successfully",
					]
				)
			else:
				steps.append(f"When {sentence.strip()}")
				steps.append("Then the expected outcome should be verified")

			scenarios.append(
				GeneratedScenario(title=f"Auto Draft Scenario {idx}", steps=steps)
			)

		return scenarios

	# endregion


def _split_sentences(text: str) -> List[str]:
	chunks = re.split(r"(?<=[.!?])\s+", text.strip())
	return [chunk for chunk in chunks if chunk]


def export_to_gherkin(scenarios: Iterable[GeneratedScenario]) -> str:
	lines = ["Feature: Auto-generated feature"]
	for scenario in scenarios:
		lines.append(scenario.to_gherkin())
		lines.append("")
	return "\n".join(lines).strip()
