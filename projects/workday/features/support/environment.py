from __future__ import annotations

from typing import Any


def after_scenario(context: Any, scenario: Any) -> None:  # pragma: no cover - Behave hook
    driver = getattr(context, "driver", None)
    if driver:
        driver.quit()
