"""NASA Image and Video Library API client."""

from __future__ import annotations

import json
import shutil
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from damage_detection.dataset.config import DatasetConfig


@dataclass(frozen=True)
class NASAImageRecord:
    """Normalized metadata for one NASA image search result."""

    nasa_id: str
    title: str
    description: str
    keywords: list[str]
    date_created: str
    center: str
    media_type: str
    preview_url: str | None = None
    asset_url: str | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)


class NASAImageClient:
    """Client for searching and downloading NASA public imagery."""

    base_url = "https://images-api.nasa.gov"
    supported_queries: tuple[str, ...] = (
        "Space Shuttle",
        "Thermal Protection System",
        "Heat Shield",
        "Spacecraft Inspection",
        "Artemis",
        "SLS",
        "Launch Vehicle",
    )

    def __init__(self, config: DatasetConfig | None = None, timeout: int = 30) -> None:
        self.config = config or DatasetConfig()
        self.timeout = timeout

    def search(self, query: str, page_size: int = 25) -> list[NASAImageRecord]:
        """Search NASA imagery and return normalized image records."""

        params = urllib.parse.urlencode(
            {"q": query, "media_type": "image", "page_size": page_size}
        )
        payload = self._request_json(f"{self.base_url}/search?{params}")
        items = payload.get("collection", {}).get("items", [])
        return [self._parse_search_item(item) for item in items]

    def retrieve_metadata(self, nasa_id: str) -> dict[str, Any]:
        """Retrieve NASA metadata for an asset by NASA ID."""

        encoded_id = urllib.parse.quote(nasa_id)
        return self._request_json(f"{self.base_url}/metadata/{encoded_id}")

    def retrieve_asset_urls(self, nasa_id: str) -> list[str]:
        """Retrieve downloadable asset URLs for a NASA asset."""

        encoded_id = urllib.parse.quote(nasa_id)
        payload = self._request_json(f"{self.base_url}/asset/{encoded_id}")
        items = payload.get("collection", {}).get("items", [])
        return [
            str(item.get("href"))
            for item in items
            if item.get("href")
            and Path(urllib.parse.urlparse(str(item.get("href"))).path).suffix.lower()
            in self.config.supported_image_formats
        ]

    def download_image(self, image_url: str, output_dir: Path, filename: str | None = None) -> Path:
        """Download an image URL to a local directory."""

        output_dir.mkdir(parents=True, exist_ok=True)
        parsed = urllib.parse.urlparse(image_url)
        suffix = Path(parsed.path).suffix.lower()
        if suffix not in self.config.supported_image_formats:
            suffix = ".jpg"
        output_name = filename or Path(parsed.path).name or f"nasa_image{suffix}"
        if Path(output_name).suffix == "":
            output_name = f"{output_name}{suffix}"
        destination = self._unique_destination(output_dir / output_name)

        with urllib.request.urlopen(image_url, timeout=self.timeout) as response:
            with destination.open("wb") as file:
                shutil.copyfileobj(response, file)
        return destination

    def save_metadata(self, records: list[NASAImageRecord], output_path: Path) -> Path:
        """Store NASA search metadata locally as JSON."""

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            json.dump([record.__dict__ for record in records], file, indent=2)
        return output_path

    def _request_json(self, url: str) -> dict[str, Any]:
        with urllib.request.urlopen(url, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _parse_search_item(item: dict[str, Any]) -> NASAImageRecord:
        data = item.get("data", [{}])[0]
        links = item.get("links", [])
        preview_url = next(
            (
                link.get("href")
                for link in links
                if link.get("render") == "image" and link.get("href")
            ),
            None,
        )
        return NASAImageRecord(
            nasa_id=str(data.get("nasa_id", "")),
            title=str(data.get("title", "")),
            description=str(data.get("description", "")),
            keywords=[str(keyword) for keyword in data.get("keywords", [])],
            date_created=str(data.get("date_created", "")),
            center=str(data.get("center", "")),
            media_type=str(data.get("media_type", "")),
            preview_url=str(preview_url) if preview_url else None,
            asset_url=str(item.get("href")) if item.get("href") else None,
            raw_metadata=item,
        )

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
