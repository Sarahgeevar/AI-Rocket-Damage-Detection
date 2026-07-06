"""JSON report generation for acquired aerospace imagery."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from damage_detection.acquisition.dataset_validator import ImageValidationResult
from damage_detection.dataset.config import DatasetConfig


class DatasetReportGenerator:
    """Generate acquisition and validation reports."""

    def __init__(self, config: DatasetConfig | None = None) -> None:
        self.config = config or DatasetConfig()

    def build_report(
        self,
        validation_results: list[ImageValidationResult],
        output_path: Path | None = None,
    ) -> dict[str, object]:
        """Build and optionally save a JSON-serializable dataset report."""

        report = {
            "image_counts": self._image_counts(validation_results),
            "category_counts": self._category_counts(validation_results),
            "average_resolution": self._average_resolution(validation_results),
            "duplicate_count": sum(result.is_duplicate for result in validation_results),
            "quality_statistics": self._quality_statistics(validation_results),
            "usefulness_statistics": self._usefulness_statistics(validation_results),
            "images": [asdict(result) for result in validation_results],
        }
        if output_path:
            self.save_report(report, output_path)
        return report

    @staticmethod
    def save_report(report: dict[str, object], output_path: Path) -> Path:
        """Save a report dictionary as JSON."""

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(report, file, indent=2)
        return output_path

    @staticmethod
    def _image_counts(results: list[ImageValidationResult]) -> dict[str, int]:
        return {
            "total": len(results),
            "valid": sum(not result.is_corrupt for result in results),
            "corrupt": sum(result.is_corrupt for result in results),
            "low_resolution": sum(result.is_low_resolution for result in results),
        }

    @staticmethod
    def _category_counts(results: list[ImageValidationResult]) -> dict[str, int]:
        counts = Counter(Path(result.path).parent.name for result in results)
        return dict(sorted(counts.items()))

    @staticmethod
    def _average_resolution(results: list[ImageValidationResult]) -> dict[str, float]:
        valid = [result for result in results if not result.is_corrupt]
        if not valid:
            return {"width": 0.0, "height": 0.0}
        return {
            "width": round(sum(result.width for result in valid) / len(valid), 2),
            "height": round(sum(result.height for result in valid) / len(valid), 2),
        }

    @staticmethod
    def _quality_statistics(results: list[ImageValidationResult]) -> dict[str, float]:
        if not results:
            return {"min": 0.0, "max": 0.0, "average": 0.0}
        scores = [result.quality_score for result in results]
        return {
            "min": min(scores),
            "max": max(scores),
            "average": round(sum(scores) / len(scores), 2),
        }

    @staticmethod
    def _usefulness_statistics(results: list[ImageValidationResult]) -> dict[str, object]:
        labels = Counter(result.usefulness_label for result in results)
        scores = [result.usefulness_score for result in results]
        average = round(sum(scores) / len(scores), 2) if scores else 0.0
        return {
            "labels": dict(sorted(labels.items())),
            "average_score": average,
        }
