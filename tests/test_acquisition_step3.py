"""Step 3 tests for image acquisition, validation, scoring, and reports."""

from __future__ import annotations

import io
import json
from pathlib import Path

import cv2
import numpy as np

from damage_detection.acquisition.dataset_report import DatasetReportGenerator
from damage_detection.acquisition.dataset_validator import DatasetValidator
from damage_detection.acquisition.nasa_client import NASAImageClient
from damage_detection.dataset.config import DatasetConfig


class FakeResponse:
    """Minimal context manager response for urllib test doubles."""

    def __init__(self, payload: bytes) -> None:
        self.payload = io.BytesIO(payload)

    def read(self) -> bytes:
        return self.payload.read()

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_nasa_api_client_parses_search_results(monkeypatch, tmp_path: Path) -> None:
    payload = {
        "collection": {
            "items": [
                {
                    "href": "https://images-api.nasa.gov/asset/abc",
                    "data": [
                        {
                            "nasa_id": "abc",
                            "title": "Space Shuttle tile inspection",
                            "description": "Close-up thermal protection tile imagery.",
                            "keywords": ["Space Shuttle", "tile", "inspection"],
                            "date_created": "2011-01-01T00:00:00Z",
                            "center": "KSC",
                            "media_type": "image",
                        }
                    ],
                    "links": [
                        {
                            "href": "https://example.com/abc.jpg",
                            "render": "image",
                        }
                    ],
                }
            ]
        }
    }

    def fake_urlopen(url: str, timeout: int = 30) -> FakeResponse:
        return FakeResponse(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = NASAImageClient(DatasetConfig(project_root=tmp_path))
    records = client.search("Space Shuttle", page_size=1)

    assert len(records) == 1
    assert records[0].nasa_id == "abc"
    assert records[0].preview_url == "https://example.com/abc.jpg"
    assert "tile" in records[0].keywords


def test_validation_logic_detects_quality_duplicates_and_corruption(tmp_path: Path) -> None:
    config = DatasetConfig(project_root=tmp_path)
    validator = DatasetValidator(config, minimum_resolution=(300, 300))
    image_a = tmp_path / "heat_shield_tile.jpg"
    image_b = tmp_path / "heat_shield_tile_copy.jpg"
    corrupt = tmp_path / "broken.jpg"

    image = np.full((500, 500, 3), 180, dtype=np.uint8)
    cv2.imwrite(str(image_a), image)
    image_b.write_bytes(image_a.read_bytes())
    corrupt.write_text("not an image", encoding="utf-8")

    results = validator.validate_images([image_a, image_b, corrupt])

    assert sum(result.is_duplicate for result in results) == 2
    assert any(result.is_corrupt for result in results)
    assert all(0.0 <= result.quality_score <= 100.0 for result in results)


def test_usefulness_scoring_labels_high_medium_low(tmp_path: Path) -> None:
    validator = DatasetValidator(DatasetConfig(project_root=tmp_path))

    high = validator.usefulness_score(
        tmp_path / "inspection.jpg",
        {"description": "Close-up heat shield tile spacecraft surface inspection"},
    )
    medium = validator.usefulness_score(
        tmp_path / "rocket_body.jpg",
        {"description": "Launch vehicle rocket body image"},
    )
    low = validator.usefulness_score(
        tmp_path / "distant_launch.jpg",
        {"description": "Distant launch photo with unrelated earth background"},
    )

    assert validator.usefulness_label(high) == "high"
    assert validator.usefulness_label(medium) == "medium"
    assert validator.usefulness_label(low) == "low"


def test_report_generation_writes_expected_json(tmp_path: Path) -> None:
    config = DatasetConfig(project_root=tmp_path)
    validator = DatasetValidator(config)
    report_generator = DatasetReportGenerator(config)
    image_path = tmp_path / "Artemis" / "spacecraft_surface.jpg"
    image_path.parent.mkdir()
    cv2.imwrite(str(image_path), np.full((400, 600, 3), 220, dtype=np.uint8))

    results = validator.validate_images(
        [image_path],
        metadata_by_filename={
            image_path.name: {"description": "spacecraft surface inspection"}
        },
    )
    output_path = tmp_path / "report.json"
    report = report_generator.build_report(results, output_path)

    assert output_path.exists()
    assert report["image_counts"]["total"] == 1
    assert report["category_counts"]["Artemis"] == 1
    assert report["duplicate_count"] == 0
    assert report["usefulness_statistics"]["labels"]["high"] == 1
