"""Metadata storage for aerospace imagery datasets."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from damage_detection.dataset.config import DatasetConfig


@dataclass
class ImageMetadata:
    """Metadata describing one image in the dataset."""

    filename: str
    source: str
    category: str
    width: int
    height: int
    file_size: int
    download_date: str
    preprocessing_status: str
    original_path: str
    processed_path: str | None = None


class MetadataManager:
    """Create and persist image metadata in JSON and CSV formats."""

    fieldnames = [
        "filename",
        "source",
        "category",
        "width",
        "height",
        "file_size",
        "download_date",
        "preprocessing_status",
        "original_path",
        "processed_path",
    ]

    def __init__(self, config: DatasetConfig | None = None) -> None:
        self.config = config or DatasetConfig()
        self.records: list[ImageMetadata] = []

    @staticmethod
    def timestamp() -> str:
        """Return an ISO 8601 UTC timestamp."""

        return datetime.now(timezone.utc).isoformat()

    def create_record(
        self,
        image_path: Path,
        source: str,
        category: str,
        width: int,
        height: int,
        preprocessing_status: str,
        processed_path: Path | None = None,
    ) -> ImageMetadata:
        """Create a metadata record from an inspected image file."""

        return ImageMetadata(
            filename=image_path.name,
            source=source,
            category=category,
            width=width,
            height=height,
            file_size=image_path.stat().st_size,
            download_date=self.timestamp(),
            preprocessing_status=preprocessing_status,
            original_path=str(image_path),
            processed_path=str(processed_path) if processed_path else None,
        )

    def add_record(self, record: ImageMetadata) -> None:
        """Add a metadata record to the in-memory collection."""

        self.records.append(record)

    def extend(self, records: Iterable[ImageMetadata]) -> None:
        """Add multiple metadata records."""

        self.records.extend(records)

    def save_json(self, path: Path | None = None) -> Path:
        """Save metadata records as JSON."""

        output_path = path or self.config.metadata_json_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            json.dump([asdict(record) for record in self.records], file, indent=2)
        return output_path

    def save_csv(self, path: Path | None = None) -> Path:
        """Save metadata records as CSV."""

        output_path = path or self.config.metadata_csv_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writeheader()
            for record in self.records:
                writer.writerow(asdict(record))
        return output_path

    def save_all(self) -> tuple[Path, Path]:
        """Save metadata to both JSON and CSV files."""

        return self.save_json(), self.save_csv()
