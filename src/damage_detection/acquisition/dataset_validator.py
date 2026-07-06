"""Dataset validation and usefulness scoring for acquired imagery."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from PIL import Image, UnidentifiedImageError

from damage_detection.dataset.config import DatasetConfig


@dataclass(frozen=True)
class ImageValidationResult:
    """Validation and scoring result for one acquired image."""

    path: str
    filename: str
    width: int
    height: int
    file_size: int
    is_corrupt: bool
    is_duplicate: bool
    is_low_resolution: bool
    quality_score: float
    usefulness_score: float
    usefulness_label: str
    notes: list[str] = field(default_factory=list)


class DatasetValidator:
    """Validate acquired images and score usefulness for damage detection."""

    high_value_terms: tuple[str, ...] = (
        "close-up",
        "closeup",
        "inspection",
        "heat shield",
        "thermal protection",
        "tile",
        "tiles",
        "spacecraft surface",
        "surface",
        "damage",
        "repair",
    )
    medium_value_terms: tuple[str, ...] = (
        "rocket body",
        "launch vehicle",
        "booster",
        "fuselage",
        "external tank",
        "orbiter",
        "sls",
        "artemis",
    )
    low_value_terms: tuple[str, ...] = (
        "distant",
        "distant launch",
        "liftoff",
        "artist",
        "planet",
        "nebula",
        "galaxy",
        "earth",
    )

    def __init__(
        self,
        config: DatasetConfig | None = None,
        minimum_resolution: tuple[int, int] = (300, 300),
    ) -> None:
        self.config = config or DatasetConfig()
        self.minimum_resolution = minimum_resolution

    def validate_images(
        self,
        image_paths: Iterable[Path],
        metadata_by_filename: dict[str, dict[str, object]] | None = None,
    ) -> list[ImageValidationResult]:
        """Validate image files and flag exact duplicates."""

        metadata_by_filename = metadata_by_filename or {}
        paths = list(image_paths)
        duplicate_paths = self._duplicate_paths(paths)
        return [
            self.validate_image(
                path,
                path in duplicate_paths,
                metadata_by_filename.get(path.name, {}),
            )
            for path in paths
        ]

    def validate_image(
        self,
        image_path: Path,
        is_duplicate: bool = False,
        metadata: dict[str, object] | None = None,
    ) -> ImageValidationResult:
        """Validate one image and compute quality and usefulness scores."""

        metadata = metadata or {}
        notes: list[str] = []
        width = 0
        height = 0
        is_corrupt = False

        try:
            with Image.open(image_path) as image:
                image.verify()
            with Image.open(image_path) as image:
                width, height = image.size
        except (OSError, UnidentifiedImageError):
            is_corrupt = True
            notes.append("corrupt_or_unreadable")

        file_size = image_path.stat().st_size if image_path.exists() else 0
        is_low_resolution = (
            width < self.minimum_resolution[0] or height < self.minimum_resolution[1]
        )
        if is_low_resolution:
            notes.append("low_resolution")
        if is_duplicate:
            notes.append("duplicate")

        quality_score = self.quality_score(
            width=width,
            height=height,
            is_corrupt=is_corrupt,
            is_duplicate=is_duplicate,
        )
        usefulness_score = self.usefulness_score(image_path, metadata)
        usefulness_label = self.usefulness_label(usefulness_score)

        return ImageValidationResult(
            path=str(image_path),
            filename=image_path.name,
            width=width,
            height=height,
            file_size=file_size,
            is_corrupt=is_corrupt,
            is_duplicate=is_duplicate,
            is_low_resolution=is_low_resolution,
            quality_score=quality_score,
            usefulness_score=usefulness_score,
            usefulness_label=usefulness_label,
            notes=notes,
        )

    def quality_score(
        self,
        width: int,
        height: int,
        is_corrupt: bool,
        is_duplicate: bool = False,
    ) -> float:
        """Compute a quality score from resolution, aspect ratio, and integrity."""

        if is_corrupt:
            return 0.0

        min_width, min_height = self.minimum_resolution
        megapixels = (width * height) / 1_000_000
        resolution_score = min(40.0, (megapixels / 1.0) * 40.0)
        if width >= min_width and height >= min_height:
            resolution_score = max(resolution_score, 25.0)

        aspect_ratio = width / height if height else 0.0
        aspect_score = 25.0 if 0.4 <= aspect_ratio <= 2.5 else 10.0
        integrity_score = 35.0
        if is_duplicate:
            integrity_score -= 10.0
        return round(max(0.0, resolution_score + aspect_score + integrity_score), 2)

    def usefulness_score(self, image_path: Path, metadata: dict[str, object]) -> float:
        """Score likely usefulness for future rocket damage detection."""

        text = self._combined_text(image_path, metadata)
        score = 20.0

        if any(term in text for term in self.high_value_terms):
            score += 60.0
        if any(term in text for term in self.medium_value_terms):
            score += 35.0
        if any(term in text for term in self.low_value_terms):
            score -= 20.0

        return round(min(100.0, max(0.0, score)), 2)

    @staticmethod
    def usefulness_label(score: float) -> str:
        """Return a human-readable usefulness label."""

        if score >= 70.0:
            return "high"
        if score >= 40.0:
            return "medium"
        return "low"

    def _duplicate_paths(self, image_paths: Iterable[Path]) -> set[Path]:
        hashes: dict[str, list[Path]] = {}
        for image_path in image_paths:
            if image_path.is_file():
                try:
                    hashes.setdefault(self._file_hash(image_path), []).append(image_path)
                except OSError:
                    continue
        return {
            path
            for duplicate_group in hashes.values()
            if len(duplicate_group) > 1
            for path in duplicate_group
        }

    @staticmethod
    def _file_hash(image_path: Path) -> str:
        digest = hashlib.sha256()
        with image_path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _combined_text(image_path: Path, metadata: dict[str, object]) -> str:
        metadata_values: list[str] = [image_path.stem.replace("_", " ")]
        for value in metadata.values():
            if isinstance(value, list):
                metadata_values.extend(str(item) for item in value)
            else:
                metadata_values.append(str(value))
        return " ".join(metadata_values).lower()
