"""Step 2 smoke tests for the aerospace dataset manager."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from damage_detection.dataset.config import DatasetConfig
from damage_detection.dataset.data_sources import LocalImageImportSource
from damage_detection.dataset.dataset_manager import DatasetManager
from damage_detection.dataset.image_processor import ImageProcessor


def test_configuration_loads(tmp_path: Path) -> None:
    config = DatasetConfig(project_root=tmp_path)

    assert config.raw_dir == tmp_path / "data" / "raw"
    assert ".jpg" in config.supported_image_formats
    assert config.image_size == (224, 224)


def test_dataset_folders_are_created(tmp_path: Path) -> None:
    config = DatasetConfig(project_root=tmp_path)
    DatasetManager(config)

    assert config.raw_dir.exists()
    assert (config.raw_dir / "Falcon9").exists()
    assert config.processed_dir.exists()
    assert config.metadata_dir.exists()
    assert config.logs_dir.exists()


def test_image_processing_functions_run(tmp_path: Path) -> None:
    config = DatasetConfig(project_root=tmp_path)
    processor = ImageProcessor(config)
    source_image = tmp_path / "sample.jpg"
    processed_image = tmp_path / "processed.jpg"

    image = np.full((32, 48, 3), 127, dtype=np.uint8)
    cv2.imwrite(str(source_image), image)

    assert processor.validate_file(source_image)
    assert processor.get_dimensions(source_image) == (48, 32)
    assert processor.convert_to_rgb(source_image).shape == (32, 48, 3)
    assert processor.convert_to_grayscale(source_image).shape == (32, 48)
    assert processor.normalize_image(image).max() <= 1.0

    processor.preprocess_image(source_image, processed_image)
    assert processed_image.exists()


def test_metadata_generation_works(tmp_path: Path) -> None:
    config = DatasetConfig(project_root=tmp_path)
    manager = DatasetManager(config)
    local_source_dir = tmp_path / "manual_images"
    local_source_dir.mkdir()
    sample_image = local_source_dir / "inspection.jpg"

    image = np.full((24, 24, 3), 200, dtype=np.uint8)
    cv2.imwrite(str(sample_image), image)

    source = LocalImageImportSource(local_source_dir, config=config)
    records = manager.ingest_from_source(source, category="Falcon9", limit=1)

    assert len(records) == 1
    assert records[0].category == "Falcon9"
    assert records[0].preprocessing_status == "processed"
    assert config.metadata_json_path.exists()
    assert config.metadata_csv_path.exists()
    assert config.summary_json_path.exists()
