"""AI-assisted analytics for test execution telemetry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

try:
    import numpy as np
except ImportError:  # pragma: no cover - optional dependency
    np = None  # type: ignore[assignment]

try:
    import pandas as pd
except ImportError:  # pragma: no cover - optional dependency
    pd = None  # type: ignore[assignment]

try:
    from loguru import logger  # type: ignore
except ImportError:  # pragma: no cover
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
try:
    from sklearn.ensemble import IsolationForest  # type: ignore
except ImportError:  # pragma: no cover
    IsolationForest = None


class TestRunAnalytics:
    """Aggregate run history and surface potential anomalies or flaky tests."""

    def __init__(self, history_path: str = "reports/run_history.json"):
        self.history_path = Path(history_path)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

    def record_run(self, report: Dict) -> None:
        data = self._load_history()
        data.append(report)
        self._save_history(data)

    def detect_anomalies(self, feature_keys: Optional[List[str]] = None):
        if pd is None or IsolationForest is None:
            logger.warning("Analytics dependencies missing; skipping anomaly detection")
            return []
        data = self._load_history()
        if not data:
            logger.warning("No history available to detect anomalies")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        feature_keys = feature_keys or ["duration", "failed", "skipped"]
        missing = [key for key in feature_keys if key not in df.columns]
        if missing:
            logger.warning("Missing features for anomaly detection", missing=missing)
            return pd.DataFrame()

        features = df[feature_keys].fillna(0)
        model = IsolationForest(contamination=0.1, random_state=42)
        df["anomaly_score"] = model.fit_predict(features)
        anomalies = df[df["anomaly_score"] == -1]
        logger.info("Anomaly detection completed", count=len(anomalies))
        return anomalies

    def flaky_test_candidates(self, min_failures: int = 2):
        if pd is None:
            logger.warning("Pandas not installed; skipping flaky test analysis")
            return []
        data = self._load_history()
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        if "failed_tests" not in df.columns:
            return pd.DataFrame()

        exploded = df.explode("failed_tests").dropna(subset=["failed_tests"])
        summary = (
            exploded.groupby("failed_tests")
            .size()
            .reset_index(name="fail_count")
            .query("fail_count >= @min_failures")
            .sort_values("fail_count", ascending=False)
        )
        return summary

    def retry_recommendations(self) -> List[str]:
        data = self._load_history()
        if not data:
            return []
        if pd is None or np is None:
            logger.warning("Analytics dependencies missing; skipping retry recommendation analysis")
            return []
        df = pd.DataFrame(data)
        if {"failed", "passed"}.issubset(df.columns):
            df["failure_ratio"] = df["failed"] / (df["failed"] + df["passed"]).replace(0, np.nan)
            risky_runs = df[df["failure_ratio"].fillna(0) > 0.3]
            return [f"Run {row['run_id']} had high failure ratio {row['failure_ratio']:.2f}" for _, row in risky_runs.iterrows()]
        return []

    def _load_history(self) -> List[Dict]:
        if self.history_path.exists():
            with self.history_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        return []

    def _save_history(self, data: List[Dict]) -> None:
        with self.history_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
