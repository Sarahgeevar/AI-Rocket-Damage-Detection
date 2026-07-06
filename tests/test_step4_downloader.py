"""Step 4 tests for the real NASA image downloader."""

from __future__ import annotations

import io
import json
from pathlib import Path

from PIL import Image
import pytest

from damage_detection.acquisition.nasa_client import NASAImageRecord
from damage_detection.acquisition.nasa_downloader import NASAImageDownloader
from damage_detection.dataset.config import DatasetConfig


class FakeNASAClient:
    """Small NASA client test double."""

    def __init__(self, records: list[NASAImageRecord]) -> None:
        self.records = records

    def search(self, query: str, page_size: int = 25) -> list[NASAImageRecord]:
        return self.records[:page_size]

    def retrieve_asset_urls(self, nasa_id: str) -> list[str]:
        return [f"https://example.com/{nasa_id}.jpg"]


class FakeResponse:
    """File-like context manager for mocked downloads."""

    def __init__(self, payload: bytes) -> None:
        self.payload = io.BytesIO(payload)

    def read(self, size: int = -1) -> bytes:
        return self.payload.read(size)

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def image_bytes(color: tuple[int, int, int] = (120, 120, 120)) -> bytes:
    buffer = io.BytesIO()
    image = Image.new("RGB", (64, 64), color=color)
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_downloader_saves_images_and_metadata(monkeypatch, tmp_path: Path) -> None:
    records = [
        NASAImageRecord(
            nasa_id="tile-001",
            title="Space Shuttle tile inspection",
            description="Thermal protection system tile inspection.",
            keywords=["tile"],
            date_created="2011-01-01T00:00:00Z",
            center="KSC",
            media_type="image",
            preview_url="https://example.com/tile-001.jpg",
        )
    ]

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda url, timeout=30: FakeResponse(image_bytes()),
    )

    config = DatasetConfig(project_root=tmp_path)
    downloader = NASAImageDownloader(config=config, client=FakeNASAClient(records))
    downloaded = downloader.download(
        query="space shuttle tile inspection",
        category="Space_Shuttle",
        limit=25,
    )

    assert len(downloaded) == 1
    assert (config.raw_dir / "Space_Shuttle" / downloaded[0].filename).exists()
    metadata_files = list((config.metadata_dir / "downloads").glob("*.json"))
    assert len(metadata_files) == 1
    payload = json.loads(metadata_files[0].read_text(encoding="utf-8"))
    assert payload[0]["filename"] == downloaded[0].filename
    assert payload[0]["NASA title"] == "Space Shuttle tile inspection"
    assert payload[0]["NASA description"] == "Thermal protection system tile inspection."
    assert payload[0]["URL"] == "https://example.com/tile-001.jpg"
    assert payload[0]["category"] == "Space_Shuttle"


def test_downloader_skips_duplicate_images(monkeypatch, tmp_path: Path) -> None:
    records = [
        NASAImageRecord(
            nasa_id=f"duplicate-{index}",
            title="Duplicate image",
            description="Same NASA image bytes.",
            keywords=[],
            date_created="2011-01-01T00:00:00Z",
            center="KSC",
            media_type="image",
            preview_url=f"https://example.com/duplicate-{index}.jpg",
        )
        for index in range(2)
    ]

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda url, timeout=30: FakeResponse(image_bytes()),
    )

    config = DatasetConfig(project_root=tmp_path)
    downloader = NASAImageDownloader(config=config, client=FakeNASAClient(records))
    downloaded = downloader.download("duplicate query", "Artemis", limit=2)

    assert len(downloaded) == 1
    assert len(list((config.raw_dir / "Artemis").glob("*.jpg"))) == 1


def test_downloader_skips_corrupted_files(monkeypatch, tmp_path: Path) -> None:
    records = [
        NASAImageRecord(
            nasa_id="broken",
            title="Broken image",
            description="Invalid file should be skipped.",
            keywords=[],
            date_created="2011-01-01T00:00:00Z",
            center="KSC",
            media_type="image",
            preview_url="https://example.com/broken.jpg",
        )
    ]

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda url, timeout=30: FakeResponse(b"not an image"),
    )

    config = DatasetConfig(project_root=tmp_path)
    downloader = NASAImageDownloader(config=config, client=FakeNASAClient(records))
    downloaded = downloader.download("broken query", "SLS", limit=1)

    assert downloaded == []
    assert list((config.raw_dir / "SLS").glob("*.jpg")) == []


def test_downloader_rejects_invalid_category(tmp_path: Path) -> None:
    config = DatasetConfig(project_root=tmp_path)
    downloader = NASAImageDownloader(config=config, client=FakeNASAClient([]))

    with pytest.raises(ValueError, match="Unsupported category"):
        downloader.download("query", "InvalidCategory", limit=1)
