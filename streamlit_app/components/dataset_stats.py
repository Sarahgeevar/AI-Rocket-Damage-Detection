"""Dataset statistics helpers for the Streamlit dashboard."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import streamlit as st

from damage_detection.annotation import AnnotationManager
from damage_detection.annotation.label_schema import get_damage_class
from damage_detection.dataset.config import DatasetConfig
from streamlit_app.components.image_viewer import list_raw_images


def compute_dataset_stats(
    config: DatasetConfig,
    manager: AnnotationManager,
) -> dict[str, object]:
    """Compute image and annotation statistics for dashboard display."""

    images = list_raw_images(config)
    annotated_images = 0
    class_distribution: Counter[str] = Counter()

    for image_path in images:
        annotation_path = manager.annotation_path_for(image_path)
        if not annotation_path.exists():
            continue
        image_annotations = manager.load_annotations(annotation_path)
        if image_annotations.annotations:
            annotated_images += 1
        for annotation in image_annotations.annotations:
            class_distribution[get_damage_class(annotation.damage_class).name] += 1

    return {
        "total_images": len(images),
        "annotated_images": annotated_images,
        "unannotated_images": len(images) - annotated_images,
        "class_distribution": dict(sorted(class_distribution.items())),
    }


def annotation_files_with_existing_images(
    manager: AnnotationManager,
) -> list[Path]:
    """Return annotation JSON files whose referenced images still exist."""

    valid_paths: list[Path] = []
    for annotation_path in sorted(manager.annotation_dir.glob("*.json")):
        image_annotations = manager.load_annotations(annotation_path)
        if Path(image_annotations.image_path).exists():
            valid_paths.append(annotation_path)
    return valid_paths


def render_dataset_stats(stats: dict[str, object]) -> None:
    """Render dataset statistics in Streamlit."""

    st.subheader("Dataset Statistics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Images", int(stats["total_images"]))
    col2.metric("Annotated Images", int(stats["annotated_images"]))
    col3.metric("Unannotated Images", int(stats["unannotated_images"]))

    distribution = stats["class_distribution"]
    if distribution:
        st.bar_chart(distribution)
    else:
        st.caption("No damage class annotations yet.")
