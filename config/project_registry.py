"""Registry describing available automation projects within the framework."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional


@dataclass(frozen=True)
class ProjectDefinition:
    name: str
    """Human-friendly name for the project."""

    key: str
    """CLI key used to refer to the project."""

    features_path: Path
    """Path containing the project's Behave features."""

    env_file: Optional[Path] = None
    """Optional .env file to load before running the suite."""

    description: str = ""
    """Short description of the project under test."""


def _default_registry() -> Dict[str, ProjectDefinition]:
    root = Path(__file__).resolve().parent.parent
    core_features = root / "features"

    return {
        "core": ProjectDefinition(
            name="Core Behave Suite",
            key="core",
            features_path=core_features,
            env_file=root / ".env",
            description="Default features located under the shared 'features' folder.",
        ),
        "workday": ProjectDefinition(
            name="Workday QA Smoke",
            key="workday",
            features_path=root / "projects" / "workday" / "features",
            env_file=root / "projects" / "workday" / ".env.workday",
            description="Focused Workday login and skip-device validation flows.",
        ),
        "saucedemo": ProjectDefinition(
            name="Saucedemo Checkout",
            key="saucedemo",
            features_path=root / "projects" / "saucedemo" / "features",
            env_file=root / "projects" / "saucedemo" / ".env.saucedemo",
            description="Saucedemo sample flows covering login and inventory interactions.",
        ),
        "auto_completion_projcet": ProjectDefinition(
            name="Auto Completion Project",
            key="auto_completion_projcet",
            features_path=root / "projects" / "auto_completion_projcet" / "features",
            env_file=root / "projects" / "auto_completion_projcet" / ".env.auto_completion_projcet",
            description="Skeleton project ready for user-provided auto-completion application flows.",
        ),
    }


_PROJECTS = _default_registry()


def list_projects() -> Iterable[ProjectDefinition]:
    """Return all registered projects."""

    return _PROJECTS.values()


def get_project(key: Optional[str]) -> ProjectDefinition:
    """Return project definition by key, defaulting to the core suite."""

    if not key:
        return _PROJECTS["core"]

    try:
        return _PROJECTS[key]
    except KeyError as exc:  # pragma: no cover - defensive guard
        available = ", ".join(sorted(_PROJECTS))
        raise ValueError(f"Unknown project '{key}'. Available projects: {available}") from exc
