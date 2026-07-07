"""YOLO label export for aerospace damage annotations."""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

from damage_detection.annotation.annotation_manager import (
    AnnotationManager,
    ImageAnnotations,
)
from damage_detection.annotation.label_schema import get_damage_class
from damage_detection.dataset.config import DatasetConfig


class YOLOExporter:
    """Export JSON annotations to YOLO image and label folders."""

    def __init__(
        self,
        config: DatasetConfig | None = None,
        annotation_manager: AnnotationManager | None = None,
    ) -> None:
        self.config = config or DatasetConfig()
        self.annotation_manager = annotation_manager or AnnotationManager(self.config)
        self.yolo_dir = self.config.data_dir / "annotations" / "yolo"
        self.images_dir = self.yolo_dir / "images"
        self.labels_dir = self.yolo_dir / "labels"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.labels_dir.mkdir(parents=True, exist_ok=True)

    def export_to_yolo(
        self,
        annotation_paths: list[Path] | None = None,
        copy_images: bool = True,
    ) -> list[Path]:
        """Convert JSON annotation files into normalized YOLO label files."""

        paths = annotation_paths or sorted(self.annotation_manager.annotation_dir.glob("*.json"))
        exported_labels: list[Path] = []

        for annotation_path in paths:
            image_annotations = self.annotation_manager.load_annotations(annotation_path)
            self.annotation_manager.validate_annotations(image_annotations)
            image_path = Path(image_annotations.image_path)

            with Image.open(image_path) as image:
                image_width, image_height = image.size

            label_path = self.labels_dir / f"{image_path.stem}.txt"
            label_path.write_text(
                self._to_yolo_text(image_annotations, image_width, image_height),
                encoding="utf-8",
            )
            exported_labels.append(label_path)

            if copy_images:
                shutil.copy2(image_path, self.images_dir / image_path.name)

        return exported_labels

    @staticmethod
    def _to_yolo_text(
        image_annotations: ImageAnnotations,
        image_width: int,
        image_height: int,
    ) -> str:
        lines: list[str] = []
        for annotation in image_annotations.annotations:
            damage_class = get_damage_class(annotation.damage_class)
            bbox = annotation.bbox
            center_x = (bbox.x + bbox.width / 2.0) / image_width
            center_y = (bbox.y + bbox.height / 2.0) / image_height
            width = bbox.width / image_width
            height = bbox.height / image_height
            lines.append(
                f"{damage_class.id} "
                f"{center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}"
            )
        return "\n".join(lines) + ("\n" if lines else "")
