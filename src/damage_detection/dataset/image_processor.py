"""Image validation and preprocessing utilities."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from damage_detection.dataset.config import DatasetConfig


class ImageProcessor:
    """Validate, inspect, and preprocess aerospace imagery."""

    def __init__(self, config: DatasetConfig | None = None) -> None:
        self.config = config or DatasetConfig()

    def is_supported_format(self, image_path: Path) -> bool:
        """Return whether the file extension is a supported image format."""

        return image_path.suffix.lower() in self.config.supported_image_formats

    def validate_file(self, image_path: Path) -> bool:
        """Return True when a path exists, has an image extension, and opens."""

        if not image_path.is_file() or not self.is_supported_format(image_path):
            return False
        return not self.is_corrupt(image_path)

    def is_corrupt(self, image_path: Path) -> bool:
        """Detect unreadable or truncated image files."""

        try:
            with Image.open(image_path) as image:
                image.verify()
            cv_image = cv2.imread(str(image_path))
            return cv_image is None
        except (OSError, UnidentifiedImageError):
            return True

    def get_dimensions(self, image_path: Path) -> tuple[int, int]:
        """Return image width and height."""

        with Image.open(image_path) as image:
            return image.size

    def resize_image(
        self,
        image_path: Path,
        output_path: Path,
        size: tuple[int, int] | None = None,
    ) -> Path:
        """Resize an image and save it to the requested output path."""

        target_size = size or self.config.image_size
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"OpenCV could not read image: {image_path}")
        resized = cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(output_path), resized)
        return output_path

    def convert_to_rgb(self, image_path: Path) -> np.ndarray:
        """Load an image with OpenCV and return an RGB array."""

        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"OpenCV could not read image: {image_path}")
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def convert_to_grayscale(self, image_path: Path) -> np.ndarray:
        """Load an image and return a grayscale array."""

        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"OpenCV could not read image: {image_path}")
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def normalize_image(self, image: np.ndarray) -> np.ndarray:
        """Normalize image pixel values to the 0.0 to 1.0 range."""

        return image.astype(np.float32) / 255.0

    def file_hash(self, image_path: Path) -> str:
        """Return a SHA-256 hash for exact duplicate detection."""

        digest = hashlib.sha256()
        with image_path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def find_duplicates(self, image_paths: Iterable[Path]) -> dict[str, list[Path]]:
        """Group exact duplicate files by SHA-256 hash."""

        hashes: dict[str, list[Path]] = {}
        for image_path in image_paths:
            if self.validate_file(image_path):
                hashes.setdefault(self.file_hash(image_path), []).append(image_path)
        return {file_hash: paths for file_hash, paths in hashes.items() if len(paths) > 1}

    def preprocess_image(
        self,
        image_path: Path,
        output_path: Path,
        grayscale: bool = False,
    ) -> Path:
        """Validate, resize, optionally grayscale, and save a processed image."""

        if not self.validate_file(image_path):
            raise ValueError(f"Invalid or corrupt image file: {image_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"OpenCV could not read image: {image_path}")

        resized = cv2.resize(image, self.config.image_size, interpolation=cv2.INTER_AREA)
        if grayscale:
            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(str(output_path), resized)
        return output_path
