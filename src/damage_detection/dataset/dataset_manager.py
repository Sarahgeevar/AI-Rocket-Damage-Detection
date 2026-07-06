"""High-level dataset manager for aerospace imagery."""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path

from damage_detection.dataset.config import DatasetConfig
from damage_detection.dataset.data_sources import BaseImageSource, SourceImage
from damage_detection.dataset.image_processor import ImageProcessor
from damage_detection.dataset.metadata_manager import ImageMetadata, MetadataManager


class DatasetManager:
    """Coordinate image ingestion, validation, preprocessing, and metadata."""

    def __init__(self, config: DatasetConfig | None = None) -> None:
        self.config = config or DatasetConfig()
        self.image_processor = ImageProcessor(self.config)
        self.metadata_manager = MetadataManager(self.config)
        self.initialize_folder_structure()
        self.logger = self._configure_logger()

    def initialize_folder_structure(self) -> None:
        """Create the project dataset folder structure."""

        self.config.raw_dir.mkdir(parents=True, exist_ok=True)
        for category in self.config.raw_categories:
            (self.config.raw_dir / category).mkdir(parents=True, exist_ok=True)
        self.config.processed_dir.mkdir(parents=True, exist_ok=True)
        self.config.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.config.logs_dir.mkdir(parents=True, exist_ok=True)

    def ingest_from_source(
        self,
        source: BaseImageSource,
        category: str,
        limit: int | None = None,
        preprocess: bool = True,
    ) -> list[ImageMetadata]:
        """Collect images from a source and register valid records."""

        if category not in self.config.raw_categories:
            self.logger.warning("Using non-standard category: %s", category)

        collected_images = source.collect(category=category, limit=limit)
        records = self.register_images(collected_images, preprocess=preprocess)
        self.metadata_manager.extend(records)
        self.metadata_manager.save_all()
        self.generate_summary_report()
        return records

    def register_images(
        self,
        images: list[SourceImage],
        preprocess: bool = True,
    ) -> list[ImageMetadata]:
        """Validate collected images and create metadata records."""

        records: list[ImageMetadata] = []
        for image in images:
            if not self.image_processor.validate_file(image.path):
                self.logger.warning("Skipping invalid image: %s", image.path)
                continue

            width, height = self.image_processor.get_dimensions(image.path)
            processed_path: Path | None = None
            status = "raw_validated"

            if preprocess:
                processed_path = self._processed_path_for(image.path, image.category)
                self.image_processor.preprocess_image(image.path, processed_path)
                status = "processed"

            records.append(
                self.metadata_manager.create_record(
                    image_path=image.path,
                    source=image.source,
                    category=image.category,
                    width=width,
                    height=height,
                    preprocessing_status=status,
                    processed_path=processed_path,
                )
            )
        return records

    def validate_dataset(self) -> dict[str, int]:
        """Validate all raw images and return dataset health statistics."""

        raw_images = self._raw_image_paths()
        valid_count = sum(
            1 for image_path in raw_images if self.image_processor.validate_file(image_path)
        )
        duplicate_groups = self.image_processor.find_duplicates(raw_images)
        return {
            "total_files": len(raw_images),
            "valid_images": valid_count,
            "invalid_images": len(raw_images) - valid_count,
            "duplicate_groups": len(duplicate_groups),
        }

    def dataset_statistics(self) -> dict[str, object]:
        """Return category-level counts and validation statistics."""

        raw_images = self._raw_image_paths()
        counts = Counter(path.parent.name for path in raw_images)
        validation = self.validate_dataset()
        return {
            "categories": dict(sorted(counts.items())),
            "validation": validation,
            "processed_images": len(self._processed_image_paths()),
            "metadata_records": len(self.metadata_manager.records),
        }

    def generate_summary_report(self, path: Path | None = None) -> Path:
        """Write a JSON dataset summary report."""

        output_path = path or self.config.summary_json_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(self.dataset_statistics(), file, indent=2)
        return output_path

    def _configure_logger(self) -> logging.Logger:
        logger = logging.getLogger("damage_detection.dataset")
        logger.setLevel(getattr(logging, self.config.log_level.upper(), logging.INFO))
        logger.propagate = False

        if not any(
            isinstance(handler, logging.FileHandler)
            and Path(handler.baseFilename) == self.config.log_path
            for handler in logger.handlers
        ):
            file_handler = logging.FileHandler(self.config.log_path)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                )
            )
            logger.addHandler(file_handler)

        return logger

    def _raw_image_paths(self) -> list[Path]:
        return sorted(
            path
            for path in self.config.raw_dir.rglob("*")
            if path.is_file()
            and path.suffix.lower() in self.config.supported_image_formats
        )

    def _processed_image_paths(self) -> list[Path]:
        return sorted(
            path
            for path in self.config.processed_dir.rglob("*")
            if path.is_file()
            and path.suffix.lower() in self.config.supported_image_formats
        )

    def _processed_path_for(self, image_path: Path, category: str) -> Path:
        category_dir = self.config.processed_dir / category
        return category_dir / f"{image_path.stem}_processed.jpg"
