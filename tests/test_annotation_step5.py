"""Step 5 tests for aerospace damage annotations and YOLO export."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
import pytest

from damage_detection.annotation import (
    Annotation,
    AnnotationManager,
    BoundingBox,
    ImageAnnotations,
    YOLOExporter,
)
from damage_detection.annotation.label_schema import DAMAGE_CLASSES
from damage_detection.dataset.config import DatasetConfig


def test_schema() -> None:
    assert len(DAMAGE_CLASSES) >= 10
    assert DAMAGE_CLASSES[0].name == "CRACK"
    assert DAMAGE_CLASSES[-1].name == "OTHER"


def test_annotation_save_load(tmp_path: Path) -> None:
    config = DatasetConfig(project_root=tmp_path)
    manager = AnnotationManager(config)
    image_path = tmp_path / "sample.jpg"
    image_path.write_bytes(b"placeholder")
    annotations = ImageAnnotations(
        image_path=str(image_path),
        annotations=[
            Annotation(
                damage_class=0,
                confidence=0.95,
                bbox=BoundingBox(x=10, y=20, width=30, height=40),
                notes="visible crack",
            )
        ],
        annotator="student",
    )

    saved_path = manager.save_annotations(annotations)
    loaded = manager.load_annotations(saved_path)

    assert loaded.image_path == str(image_path)
    assert loaded.annotator == "student"
    assert loaded.annotations[0].damage_class == 0
    assert loaded.annotations[0].bbox.width == 30
    assert loaded.annotations[0].notes == "visible crack"


def test_annotation_validation(tmp_path: Path) -> None:
    config = DatasetConfig(project_root=tmp_path)
    manager = AnnotationManager(config)

    invalid_cases = [
        Annotation(0, 0.9, BoundingBox(x=-1, y=0, width=10, height=10)),
        Annotation(0, 0.9, BoundingBox(x=0, y=0, width=0, height=10)),
        Annotation(0, 0.9, BoundingBox(x=0, y=0, width=10, height=0)),
        Annotation(999, 0.9, BoundingBox(x=0, y=0, width=10, height=10)),
    ]

    for annotation in invalid_cases:
        with pytest.raises(ValueError):
            manager.validate_annotations(
                ImageAnnotations(
                    image_path=str(tmp_path / "image.jpg"),
                    annotations=[annotation],
                )
            )


def test_yolo_export(tmp_path: Path) -> None:
    config = DatasetConfig(project_root=tmp_path)
    manager = AnnotationManager(config)
    image_path = tmp_path / "tile_damage.jpg"
    Image.new("RGB", (200, 100), color=(180, 180, 180)).save(image_path)

    annotation_file = manager.save_annotations(
        ImageAnnotations(
            image_path=str(image_path),
            annotations=[
                Annotation(
                    damage_class="TILE_DAMAGE",
                    confidence=0.88,
                    bbox=BoundingBox(x=50, y=25, width=100, height=50),
                    notes="center tile damage",
                )
            ],
            annotator="student",
        )
    )

    exporter = YOLOExporter(config, manager)
    exported = exporter.export_to_yolo([annotation_file])

    assert len(exported) == 1
    label_path = exported[0]
    assert label_path.exists()
    values = label_path.read_text(encoding="utf-8").strip().split()
    assert values[0] == "1"
    assert [float(value) for value in values[1:]] == [0.5, 0.5, 0.5, 0.5]
    assert (exporter.images_dir / image_path.name).exists()
