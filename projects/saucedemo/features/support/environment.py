from __future__ import annotations

from typing import Any


def after_scenario(context: Any, scenario: Any) -> None:  # pragma: no cover - Behave hook
    _shutdown_driver(context)


def after_feature(context: Any, feature: Any) -> None:  # pragma: no cover - Behave hook
    _shutdown_driver(context)


def _shutdown_driver(context: Any) -> None:
    driver = getattr(context, "driver", None)
    if driver:
        driver.quit()
        setattr(context, "driver", None)
