"""Centralized configuration for AI-assisted features."""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AISettings:
    """Loads AI related configuration from environment variables."""

    provider: str = os.getenv("AI_PROVIDER", "openai").lower()
    api_key: Optional[str] = os.getenv("AI_API_KEY")
    api_base: Optional[str] = os.getenv("AI_API_BASE")
    enable_nlp: bool = os.getenv("AI_ENABLE_NLP", "true").lower() == "true"
    enable_visual: bool = os.getenv("AI_ENABLE_VISUAL", "true").lower() == "true"
    enable_analytics: bool = os.getenv("AI_ENABLE_ANALYTICS", "true").lower() == "true"
    request_timeout: float = float(os.getenv("AI_REQUEST_TIMEOUT", "30"))
    max_tokens: int = int(os.getenv("AI_MAX_TOKENS", "1024"))
    opt_in_required: bool = os.getenv("AI_OPT_IN_REQUIRED", "true").lower() == "true"

    def validate(self) -> None:
        if self.opt_in_required and not self.api_key:
            raise RuntimeError(
                "AI features require an API key. Provide AI_API_KEY or disable opt-in via AI_OPT_IN_REQUIRED=false"
            )


def load_settings(validate: bool = False) -> AISettings:
    settings = AISettings()
    if validate:
        settings.validate()
    return settings
