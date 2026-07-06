"""NASA imagery downloader for the project dataset structure."""

from __future__ import annotations

import hashlib
import json
import shutil
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from damage_detection.acquisition.nasa_client import NASAImageClient, NASAImageRecord
from damage_detection.dataset.config import DatasetConfig


@dataclass(frozen=True)
class DownloadedNASAImage:
    """Metadata for one successfully downloaded NASA image."""

    filename: str
    nasa_title: str
    nasa_description: str
    url: str
    download_date: str
    category: str


class NASAImageDownloader:
    """Download NASA imagery into `data/raw/<category>/` with metadata."""

    allowed_categories: tuple[str, ...] = (
        "Falcon9",
        "Starship",
        "SLS",
        "Artemis",
        "Space_Shuttle",
        "DeltaIV",
        "AtlasV",
    )

    def __init__(
        self,
        config: DatasetConfig | None = None,
        client: NASAImageClient | None = None,
        timeout: int = 30,
    ) -> None:
        self.config = config or DatasetConfig()
        self.client = client or NASAImageClient(self.config, timeout=timeout)
        self.timeout = timeout
        self.download_metadata_dir = self.config.metadata_dir / "downloads"
        self.download_metadata_dir.mkdir(parents=True, exist_ok=True)
        for category in self.allowed_categories:
            (self.config.raw_dir / category).mkdir(parents=True, exist_ok=True)

    def download(
        self,
        query: str,
        category: str,
        limit: int = 25,
    ) -> list[DownloadedNASAImage]:
        """Search NASA and download valid, non-duplicate images."""

        self._validate_category(category)
        target_dir = self.config.raw_dir / category
        target_dir.mkdir(parents=True, exist_ok=True)

        existing_hashes = self._existing_hashes(target_dir)
        downloaded: list[DownloadedNASAImage] = []
        records = self.client.search(query, page_size=limit)

        for record in records:
            if len(downloaded) >= limit:
                break

            image_url = self._best_image_url(record)
            if not image_url:
                continue

            destination = self._destination_for(target_dir, record, image_url)
            try:
                self._download_url(image_url, destination)
            except OSError:
                destination.unlink(missing_ok=True)
                continue

            if self._is_corrupt(destination):
                destination.unlink(missing_ok=True)
                continue

            file_hash = self._file_hash(destination)
            if file_hash in existing_hashes:
                destination.unlink(missing_ok=True)
                continue

            existing_hashes.add(file_hash)
            downloaded.append(
                DownloadedNASAImage(
                    filename=destination.name,
                    nasa_title=record.title,
                    nasa_description=record.description,
                    url=image_url,
                    download_date=datetime.now(timezone.utc).isoformat(),
                    category=category,
                )
            )

        self.save_metadata(downloaded, query, category)
        return downloaded

    def save_metadata(
        self,
        records: list[DownloadedNASAImage],
        query: str,
        category: str,
    ) -> Path:
        """Save download metadata to `data/metadata/downloads/`."""

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = (
            self.download_metadata_dir
            / f"{category}_{self._slugify(query)}_{timestamp}.json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            json.dump([self._metadata_dict(record) for record in records], file, indent=2)
        return output_path

    @staticmethod
    def _metadata_dict(record: DownloadedNASAImage) -> dict[str, str]:
        return {
            "filename": record.filename,
            "NASA title": record.nasa_title,
            "NASA description": record.nasa_description,
            "URL": record.url,
            "download date": record.download_date,
            "category": record.category,
        }

    def _best_image_url(self, record: NASAImageRecord) -> str | None:
        if record.preview_url:
            return record.preview_url
        if record.nasa_id:
            asset_urls = self.client.retrieve_asset_urls(record.nasa_id)
            return asset_urls[0] if asset_urls else None
        return None

    def _download_url(self, image_url: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(image_url, timeout=self.timeout) as response:
            with destination.open("wb") as file:
                shutil.copyfileobj(response, file)

    def _destination_for(
        self,
        target_dir: Path,
        record: NASAImageRecord,
        image_url: str,
    ) -> Path:
        parsed = urllib.parse.urlparse(image_url)
        suffix = Path(parsed.path).suffix.lower()
        if suffix not in self.config.supported_image_formats:
            suffix = ".jpg"
        base_name = self._slugify(record.nasa_id or record.title or "nasa_image")
        return self._unique_destination(target_dir / f"{base_name}{suffix}")

    def _existing_hashes(self, target_dir: Path) -> set[str]:
        hashes: set[str] = set()
        for path in target_dir.iterdir():
            if path.is_file() and path.suffix.lower() in self.config.supported_image_formats:
                if not self._is_corrupt(path):
                    hashes.add(self._file_hash(path))
        return hashes

    @staticmethod
    def _is_corrupt(image_path: Path) -> bool:
        try:
            with Image.open(image_path) as image:
                image.verify()
            return False
        except (OSError, UnidentifiedImageError):
            return True

    @staticmethod
    def _file_hash(image_path: Path) -> str:
        digest = hashlib.sha256()
        with image_path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _unique_destination(destination: Path) -> Path:
        if not destination.exists():
            return destination
        counter = 1
        while True:
            candidate = destination.with_name(
                f"{destination.stem}_{counter:03d}{destination.suffix}"
            )
            if not candidate.exists():
                return candidate
            counter += 1

    @classmethod
    def _validate_category(cls, category: str) -> None:
        if category not in cls.allowed_categories:
            allowed = ", ".join(cls.allowed_categories)
            raise ValueError(f"Unsupported category '{category}'. Use one of: {allowed}")

    @staticmethod
    def _slugify(value: str) -> str:
        slug = "".join(char.lower() if char.isalnum() else "_" for char in value)
        return "_".join(part for part in slug.split("_") if part) or "nasa_image"
