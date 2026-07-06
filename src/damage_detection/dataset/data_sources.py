"""Pluggable source connectors for aerospace image ingestion."""

from __future__ import annotations

import json
import shutil
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from damage_detection.dataset.config import DatasetConfig


@dataclass(frozen=True)
class SourceImage:
    """Description of one image fetched or imported from a data source."""

    path: Path
    source: str
    category: str


class BaseImageSource(ABC):
    """Abstract interface for future aerospace imagery sources."""

    source_name: str

    def __init__(self, config: DatasetConfig | None = None) -> None:
        self.config = config or DatasetConfig()

    @abstractmethod
    def collect(self, category: str, limit: int | None = None) -> list[SourceImage]:
        """Collect images for a category and return local file references."""


class NASAImagerySource(BaseImageSource):
    """Connector for NASA's public image and video library.

    This connector uses the public NASA Images search API. It downloads image
    assets into the configured raw category folder. Network access is only used
    when this source is explicitly called.
    """

    source_name = "NASA"
    search_endpoint = "https://images-api.nasa.gov/search"

    def collect(self, category: str, limit: int | None = None) -> list[SourceImage]:
        """Download NASA image search results for a category."""

        max_items = limit or self.config.max_downloads_per_source
        query = urllib.parse.urlencode({"q": category, "media_type": "image"})
        request_url = f"{self.search_endpoint}?{query}"
        with urllib.request.urlopen(request_url, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))

        items = payload.get("collection", {}).get("items", [])[:max_items]
        image_urls = [
            link["href"]
            for item in items
            for link in item.get("links", [])
            if link.get("render") == "image" and "href" in link
        ]
        return self._download_urls(image_urls[:max_items], category)

    def _download_urls(self, urls: Iterable[str], category: str) -> list[SourceImage]:
        collected: list[SourceImage] = []
        target_dir = self.config.raw_dir / category
        target_dir.mkdir(parents=True, exist_ok=True)

        for index, url in enumerate(urls, start=1):
            suffix = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".jpg"
            if suffix not in self.config.supported_image_formats:
                suffix = ".jpg"
            destination = target_dir / f"nasa_{category.lower()}_{index:04d}{suffix}"
            urllib.request.urlretrieve(url, destination)
            collected.append(
                SourceImage(path=destination, source=self.source_name, category=category)
            )
        return collected


class PublicAerospaceCollectionSource(BaseImageSource):
    """Connector for public URL-based aerospace image collections.

    Pass a list of direct image URLs or a JSON manifest containing direct image
    URLs. This is useful for ESA, launch provider media kits, or curated public
    datasets added in future steps.
    """

    source_name = "PublicAerospaceCollection"

    def __init__(
        self,
        urls: Iterable[str] | None = None,
        manifest_path: Path | None = None,
        config: DatasetConfig | None = None,
    ) -> None:
        super().__init__(config)
        self.urls = list(urls or [])
        self.manifest_path = manifest_path

    def collect(self, category: str, limit: int | None = None) -> list[SourceImage]:
        """Download direct image URLs into a raw category folder."""

        urls = self._load_urls()
        max_items = limit or self.config.max_downloads_per_source
        target_dir = self.config.raw_dir / category
        target_dir.mkdir(parents=True, exist_ok=True)

        collected: list[SourceImage] = []
        for index, url in enumerate(urls[:max_items], start=1):
            suffix = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".jpg"
            if suffix not in self.config.supported_image_formats:
                suffix = ".jpg"
            destination = target_dir / f"public_{category.lower()}_{index:04d}{suffix}"
            urllib.request.urlretrieve(url, destination)
            collected.append(
                SourceImage(path=destination, source=self.source_name, category=category)
            )
        return collected

    def _load_urls(self) -> list[str]:
        if self.manifest_path is None:
            return self.urls
        with self.manifest_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if isinstance(payload, list):
            return [str(url) for url in payload]
        return [str(url) for url in payload.get("image_urls", [])]


class LocalImageImportSource(BaseImageSource):
    """Connector for manually collected local inspection imagery."""

    source_name = "LocalImport"

    def __init__(
        self,
        source_directory: Path,
        config: DatasetConfig | None = None,
        recursive: bool = True,
    ) -> None:
        super().__init__(config)
        self.source_directory = source_directory
        self.recursive = recursive

    def collect(self, category: str, limit: int | None = None) -> list[SourceImage]:
        """Copy local images into the managed raw category folder."""

        max_items = limit or self.config.max_downloads_per_source
        target_dir = self.config.raw_dir / category
        target_dir.mkdir(parents=True, exist_ok=True)

        images = self._iter_image_paths()
        collected: list[SourceImage] = []
        for image_path in images[:max_items]:
            destination = self._unique_destination(target_dir, image_path.name)
            shutil.copy2(image_path, destination)
            collected.append(
                SourceImage(path=destination, source=self.source_name, category=category)
            )
        return collected

    def _iter_image_paths(self) -> list[Path]:
        pattern = "**/*" if self.recursive else "*"
        paths = [
            path
            for path in self.source_directory.glob(pattern)
            if path.is_file()
            and path.suffix.lower() in self.config.supported_image_formats
        ]
        return sorted(paths)

    @staticmethod
    def _unique_destination(target_dir: Path, filename: str) -> Path:
        destination = target_dir / filename
        if not destination.exists():
            return destination

        stem = destination.stem
        suffix = destination.suffix
        counter = 1
        while True:
            candidate = target_dir / f"{stem}_{counter:03d}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1
