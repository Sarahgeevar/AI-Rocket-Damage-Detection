"""High-level aerospace image acquisition pipeline."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from damage_detection.acquisition.dataset_report import DatasetReportGenerator
from damage_detection.acquisition.dataset_validator import (
    DatasetValidator,
    ImageValidationResult,
)
from damage_detection.acquisition.nasa_client import NASAImageClient, NASAImageRecord
from damage_detection.dataset.config import DatasetConfig


class ImageAcquisitionPipeline:
    """Acquire NASA imagery, validate it, and produce local reports."""

    def __init__(
        self,
        config: DatasetConfig | None = None,
        nasa_client: NASAImageClient | None = None,
        validator: DatasetValidator | None = None,
        report_generator: DatasetReportGenerator | None = None,
    ) -> None:
        self.config = config or DatasetConfig()
        self.nasa_client = nasa_client or NASAImageClient(self.config)
        self.validator = validator or DatasetValidator(self.config)
        self.report_generator = report_generator or DatasetReportGenerator(self.config)
        self.acquisition_dir = self.config.raw_dir / "NASA"
        self.acquisition_metadata_dir = self.config.metadata_dir / "acquisition"
        self.acquisition_dir.mkdir(parents=True, exist_ok=True)
        self.acquisition_metadata_dir.mkdir(parents=True, exist_ok=True)

    def acquire_nasa_images(
        self,
        query: str,
        limit: int = 10,
        download: bool = True,
    ) -> dict[str, object]:
        """Search NASA, optionally download images, validate, and report."""

        records = self.nasa_client.search(query, page_size=limit)
        selected_records = records[:limit]
        query_slug = self._slugify(query)
        query_dir = self.acquisition_dir / query_slug
        query_dir.mkdir(parents=True, exist_ok=True)

        downloaded_paths: list[Path] = []
        metadata_by_filename: dict[str, dict[str, object]] = {}

        if download:
            for record in selected_records:
                image_url = record.preview_url
                if not image_url and record.nasa_id:
                    asset_urls = self.nasa_client.retrieve_asset_urls(record.nasa_id)
                    image_url = asset_urls[0] if asset_urls else None
                if not image_url:
                    continue

                filename = f"{self._slugify(record.nasa_id or record.title)}.jpg"
                image_path = self.nasa_client.download_image(image_url, query_dir, filename)
                downloaded_paths.append(image_path)
                metadata_by_filename[image_path.name] = asdict(record)

        metadata_path = self.acquisition_metadata_dir / f"nasa_{query_slug}_metadata.json"
        self.nasa_client.save_metadata(selected_records, metadata_path)

        validation_results = self.validator.validate_images(
            downloaded_paths,
            metadata_by_filename=metadata_by_filename,
        )
        validation_path = self.acquisition_metadata_dir / f"nasa_{query_slug}_validation.json"
        self._save_validation(validation_results, validation_path)

        report_path = self.acquisition_metadata_dir / f"nasa_{query_slug}_report.json"
        report = self.report_generator.build_report(validation_results, report_path)

        return {
            "query": query,
            "metadata_path": str(metadata_path),
            "validation_path": str(validation_path),
            "report_path": str(report_path),
            "downloaded_images": [str(path) for path in downloaded_paths],
            "report": report,
        }

    def acquire_supported_nasa_searches(
        self,
        limit_per_query: int = 5,
        download: bool = True,
    ) -> list[dict[str, object]]:
        """Run the standard Step 3 NASA search set."""

        return [
            self.acquire_nasa_images(query, limit=limit_per_query, download=download)
            for query in self.nasa_client.supported_queries
        ]

    @staticmethod
    def _save_validation(
        validation_results: list[ImageValidationResult],
        output_path: Path,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            json.dump([asdict(result) for result in validation_results], file, indent=2)
        return output_path

    @staticmethod
    def _slugify(value: str) -> str:
        slug = "".join(char.lower() if char.isalnum() else "_" for char in value)
        return "_".join(part for part in slug.split("_") if part) or "nasa_image"
