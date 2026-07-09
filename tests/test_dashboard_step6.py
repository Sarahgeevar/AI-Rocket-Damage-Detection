"""Step 6 tests for dashboard helper functions."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from damage_detection.annotation import (
    Annotation,
    AnnotationManager,
    BoundingBox,
    ImageAnnotations,
)
from damage_detection.dataset.config import DatasetConfig
from streamlit_app.components.annotation_panel import (
    annotations_to_rows,
    load_or_create_annotations,
    rows_to_annotations,
)
from streamlit_app.components.dataset_stats import (
    annotation_files_with_existing_images,
    compute_dataset_stats,
)
from streamlit_app.components.image_viewer import image_label, list_raw_images


def test_dashboard_lists_raw_images_and_labels(tmp_path: Path) -> None:
    config = DatasetConfig(project_root=tmp_path)
    image_dir = config.raw_dir / "Space_Shuttle"
    image_dir.mkdir(parents=True)
    image_path = image_dir / "tile.jpg"
    Image.new("RGB", (32, 32)).save(image_path)

    images = list_raw_images(config)

    assert images == [image_path]
    assert image_label(image_path, config) == "Space_Shuttle/tile.jpg"


def test_dashboard_annotation_row_roundtrip(tmp_path: Path) -> None:
    image_annotations = ImageAnnotations(
        image_path=str(tmp_path / "tile.jpg"),
        annotations=[
            Annotation(
                damage_class="CRACK",
                confidence=0.8,
                bbox=BoundingBox(x=1, y=2, width=3, height=4),
                notes="small crack",
            )
        ],
    )

    rows = annotations_to_rows(image_annotations)
    annotations = rows_to_annotations(rows)

    assert rows[0]["damage_class"] == "CRACK"
    assert annotations[0].damage_class == 0
    assert annotations[0].bbox.height == 4


def test_dashboard_stats_count_annotations(tmp_path: Path) -> None:
    config = DatasetConfig(project_root=tmp_path)
    manager = AnnotationManager(config)
    image_dir = config.raw_dir / "Space_Shuttle"
    image_dir.mkdir(parents=True)
    annotated = image_dir / "annotated.jpg"
    unannotated = image_dir / "unannotated.jpg"
    Image.new("RGB", (32, 32)).save(annotated)
    Image.new("RGB", (32, 32)).save(unannotated)

    manager.save_annotations(
        ImageAnnotations(
            image_path=str(annotated),
            annotations=[
                Annotation(
                    damage_class="TILE_DAMAGE",
                    confidence=1.0,
                    bbox=BoundingBox(x=1, y=1, width=10, height=10),
                )
            ],
        )
    )

    stats = compute_dataset_stats(config, manager)

    assert stats["total_images"] == 2
    assert stats["annotated_images"] == 1
    assert stats["unannotated_images"] == 1
    assert stats["class_distribution"] == {"TILE_DAMAGE": 1}


def test_dashboard_loads_blank_template_and_filters_existing_images(tmp_path: Path) -> None:
    config = DatasetConfig(project_root=tmp_path)
    manager = AnnotationManager(config)
    image_path = config.raw_dir / "SLS" / "inspection.jpg"
    image_path.parent.mkdir(parents=True)
    Image.new("RGB", (32, 32)).save(image_path)

    blank = load_or_create_annotations(manager, image_path, annotator="tester")
    saved_path = manager.save_annotations(blank)

    assert blank.annotations == []
    assert blank.annotator == "tester"
    assert annotation_files_with_existing_images(manager) == [saved_path]
