"""Persistence helpers for storing page blueprints produced by the crawler."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

DEFAULT_DIR = os.path.join("data", "blueprints")


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def build_blueprint_path(project: str, timestamp: Optional[str] = None) -> str:
    safe_project = project.replace("/", "-")
    stamped = timestamp or datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"{safe_project}_{stamped}.json"
    return os.path.join(DEFAULT_DIR, safe_project, filename)


def save_blueprint(project: str, blueprint: Dict[str, object], *, latest_symlink: bool = True) -> str:
    target_path = build_blueprint_path(project)
    directory = os.path.dirname(target_path)
    _ensure_dir(directory)
    with open(target_path, "w", encoding="utf-8") as handle:
        json.dump(blueprint, handle, indent=2)
    if latest_symlink:
        marker = os.path.join(directory, "latest.json")
        with open(marker, "w", encoding="utf-8") as handle:
            json.dump({"path": target_path}, handle, indent=2)
    return target_path


def load_blueprint(path: str) -> Dict[str, object]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_latest(project: str) -> Optional[Dict[str, object]]:
    latest_path = os.path.join(DEFAULT_DIR, project, "latest.json")
    if not os.path.exists(latest_path):
        return None
    with open(latest_path, "r", encoding="utf-8") as marker:
        payload = json.load(marker)
    target = payload.get("path")
    if not target or not os.path.exists(target):
        return None
    return load_blueprint(target)


def list_blueprints(project: str) -> List[str]:
    directory = os.path.join(DEFAULT_DIR, project)
    if not os.path.exists(directory):
        return []
    files = [
        os.path.join(directory, name)
        for name in os.listdir(directory)
        if name.endswith(".json") and name != "latest.json"
    ]
    return sorted(files)
