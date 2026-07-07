"""JSON annotation management for aerospace damage labels."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from damage_detection.annotation.label_schema import get_damage_class
from damage_detection.dataset.config import DatasetConfig


@dataclass(frozen=True)
class BoundingBox:
    """Pixel-space bounding box using top-left x/y plus width and height."""

    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class Annotation:
    """One damage annotation for an image."""

    damage_class: int | str
    confidence: float
    bbox: BoundingBox
    notes: str = ""


@dataclass(frozen=True)
class ImageAnnotations:
    """All annotations associated with one image."""

    image_path: str
    annotations: list[Annotation] = field(default_factory=list)
    annotator: str = "unassigned"
    date_created: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class AnnotationManager:
    """Save, load, and validate aerospace damage annotations as JSON."""

    def __init__(self, config: DatasetConfig | None = None) -> None:
        self.config = config or DatasetConfig()
        self.annotation_dir = self.config.data_dir / "annotations" / "json"
        self.annotation_dir.mkdir(parents=True, exist_ok=True)

    def save_annotations(
        self,
        image_annotations: ImageAnnotations,
        output_path: Path | None = None,
    ) -> Path:
        """Validate and save image annotations to JSON."""

        self.validate_annotations(image_annotations)
        path = output_path or self.annotation_path_for(image_annotations.image_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(self._to_dict(image_annotations), file, indent=2)
        return path

    def load_annotations(self, annotation_path: Path) -> ImageAnnotations:
        """Load image annotations from JSON."""

        with annotation_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return self._from_dict(payload)

    def validate_annotations(self, image_annotations: ImageAnnotations) -> None:
        """Validate class IDs, confidence values, and bounding boxes."""

        if not image_annotations.image_path:
            raise ValueError("image_path is required")

        for annotation in image_annotations.annotations:
            get_damage_class(annotation.damage_class)
            if not 0.0 <= annotation.confidence <= 1.0:
                raise ValueError("confidence must be between 0.0 and 1.0")
            bbox = annotation.bbox
            if bbox.x < 0 or bbox.y < 0:
                raise ValueError("bounding box coordinates must be non-negative")
            if bbox.width <= 0:
                raise ValueError("bounding box width must be greater than zero")
            if bbox.height <= 0:
                raise ValueError("bounding box height must be greater than zero")

    def annotation_path_for(self, image_path: str | Path) -> Path:
        """Return the default JSON annotation path for an image."""

        image = Path(image_path)
        return self.annotation_dir / f"{image.stem}.json"

    @staticmethod
    def _to_dict(image_annotations: ImageAnnotations) -> dict[str, Any]:
        return asdict(image_annotations)

    @staticmethod
    def _from_dict(payload: dict[str, Any]) -> ImageAnnotations:
        annotations = [
            Annotation(
                damage_class=annotation["damage_class"],
                confidence=float(annotation["confidence"]),
                bbox=BoundingBox(
                    x=float(annotation["bbox"]["x"]),
                    y=float(annotation["bbox"]["y"]),
                    width=float(annotation["bbox"]["width"]),
                    height=float(annotation["bbox"]["height"]),
                ),
                notes=str(annotation.get("notes", "")),
            )
            for annotation in payload.get("annotations", [])
        ]
        return ImageAnnotations(
            image_path=str(payload["image_path"]),
            annotations=annotations,
            annotator=str(payload.get("annotator", "unassigned")),
            date_created=str(payload.get("date_created", "")),
        )
