"""Visual regression helpers using Pillow with optional OpenCV enhancements."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

try:
	from loguru import logger  # type: ignore
except ImportError:  # pragma: no cover
	import logging

	logging.basicConfig(level=logging.INFO)
	logger = logging.getLogger(__name__)
try:
	from PIL import Image, ImageChops, ImageStat  # type: ignore
except ImportError:  # pragma: no cover
	Image = ImageChops = ImageStat = None

try:
	import cv2  # type: ignore
	import numpy as np  # type: ignore
except ImportError:  # pragma: no cover - optional enhanced diffing
	cv2 = None
	np = None


@dataclass
class VisualDiffResult:
	baseline_path: Path
	actual_path: Path
	diff_path: Path
	rms: float
	mse: float
	threshold_exceeded: bool
	metadata: Dict[str, float]


class VisualComparator:
	"""Compare baseline and actual screenshots with perceptual metrics."""

	def __init__(self, threshold: float = 5.0, diff_dir: Optional[Path] = None):
		self.threshold = threshold
		self.diff_dir = diff_dir or Path("visual_diffs")
		self.diff_dir.mkdir(exist_ok=True)

	def compare(self, baseline: Path, actual: Path) -> VisualDiffResult:
		if Image is None:
			raise RuntimeError("Pillow is required for visual comparison; install pillow package")
		logger.info("Running visual comparison", baseline=str(baseline), actual=str(actual))
		base_img = Image.open(baseline).convert("RGB")
		actual_img = Image.open(actual).convert("RGB")

		if base_img.size != actual_img.size:
			actual_img = actual_img.resize(base_img.size)

		diff_img = ImageChops.difference(base_img, actual_img)
		diff_stat = ImageStat.Stat(diff_img)

		mse = sum(value ** 2 for value in diff_stat.mean) / len(diff_stat.mean)
		rms = math.sqrt(sum(value ** 2 for value in diff_stat.rms) / len(diff_stat.rms))

		diff_path = self.diff_dir / f"diff_{baseline.stem}_vs_{actual.stem}.png"
		diff_img.save(diff_path)

		metadata: Dict[str, float] = {"mse": mse, "rms": rms}

		if cv2 is not None and np is not None:
			heatmap_metrics = self._compute_heatmap(base_img, actual_img, diff_path)
			metadata.update(heatmap_metrics)

		result = VisualDiffResult(
			baseline_path=baseline,
			actual_path=actual,
			diff_path=diff_path,
			rms=rms,
			mse=mse,
			threshold_exceeded=rms > self.threshold,
			metadata=metadata,
		)

		if result.threshold_exceeded:
			logger.warning("Visual diff threshold exceeded", metrics=metadata)
		else:
			logger.info("Visual diff within threshold", metrics=metadata)

		return result

	def _compute_heatmap(self, base_img: Any, actual_img: Any, diff_path: Path) -> Dict[str, float]:
		if cv2 is None or np is None:  # pragma: no cover
			raise RuntimeError("OpenCV not available")

		base_array = np.array(base_img)
		actual_array = np.array(actual_img)
		overlay = cv2.absdiff(base_array, actual_array)
		gray = cv2.cvtColor(overlay, cv2.COLOR_BGR2GRAY)
		_, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
		contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

		overlay_image = base_array.copy()
		cv2.drawContours(overlay_image, contours, -1, (0, 0, 255), 2)
		heatmap_path = self.diff_dir / f"heatmap_{diff_path.stem}.png"
		cv2.imwrite(str(heatmap_path), overlay_image)

		non_zero = cv2.countNonZero(gray)
		total_pixels = gray.size
		change_ratio = non_zero / total_pixels

		return {"heatmap_path": heatmap_path.as_posix(), "change_ratio": float(change_ratio)}
