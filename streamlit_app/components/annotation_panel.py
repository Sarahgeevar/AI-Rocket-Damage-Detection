"""Annotation editing helpers for the Streamlit dashboard."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import streamlit as st

from damage_detection.annotation import (
    Annotation,
    AnnotationManager,
    BoundingBox,
    ImageAnnotations,
)
from damage_detection.annotation.label_schema import DAMAGE_CLASSES, get_damage_class


def load_or_create_annotations(
    manager: AnnotationManager,
    image_path: Path,
    annotator: str = "dashboard",
) -> ImageAnnotations:
    """Load annotations for an image or return a blank template."""

    annotation_path = manager.annotation_path_for(image_path)
    if annotation_path.exists():
        return manager.load_annotations(annotation_path)
    return ImageAnnotations(
        image_path=str(image_path),
        annotations=[],
        annotator=annotator,
    )


def annotations_to_rows(image_annotations: ImageAnnotations) -> list[dict[str, object]]:
    """Convert annotation dataclasses to editable table rows."""

    rows: list[dict[str, object]] = []
    for annotation in image_annotations.annotations:
        damage_class = get_damage_class(annotation.damage_class)
        rows.append(
            {
                "delete": False,
                "damage_class": damage_class.name,
                "confidence": annotation.confidence,
                "x": annotation.bbox.x,
                "y": annotation.bbox.y,
                "width": annotation.bbox.width,
                "height": annotation.bbox.height,
                "notes": annotation.notes,
            }
        )
    return rows


def rows_to_annotations(rows: list[dict[str, object]]) -> list[Annotation]:
    """Convert edited table rows into annotation dataclasses."""

    annotations: list[Annotation] = []
    for row in rows:
        if bool(row.get("delete", False)):
            continue
        if _is_blank_row(row):
            continue
        damage_class = str(row.get("damage_class", "OTHER")).upper()
        annotations.append(
            Annotation(
                damage_class=get_damage_class(damage_class).id,
                confidence=float(row.get("confidence", 1.0)),
                bbox=BoundingBox(
                    x=float(row.get("x", 0.0)),
                    y=float(row.get("y", 0.0)),
                    width=float(row.get("width", 1.0)),
                    height=float(row.get("height", 1.0)),
                ),
                notes=str(row.get("notes", "")),
            )
        )
    return annotations


def _is_blank_row(row: dict[str, object]) -> bool:
    damage_class = row.get("damage_class")
    if damage_class is None:
        return True
    if isinstance(damage_class, float) and math.isnan(damage_class):
        return True
    return str(damage_class).strip() == ""


def render_damage_class_reference() -> None:
    """Display the centralized damage class schema."""

    with st.expander("Damage Classes", expanded=False):
        for damage_class in DAMAGE_CLASSES:
            st.markdown(
                f"**{damage_class.id} - {damage_class.name}**: "
                f"{damage_class.description}"
            )


def render_annotation_panel(
    manager: AnnotationManager,
    image_path: Path,
    annotator: str,
) -> ImageAnnotations:
    """Render annotation editing controls and save updates when requested."""

    image_annotations = load_or_create_annotations(manager, image_path, annotator)
    rows = annotations_to_rows(image_annotations)
    columns = ["delete", "damage_class", "confidence", "x", "y", "width", "height", "notes"]

    st.subheader("Annotations")
    edited = st.data_editor(
        pd.DataFrame(rows, columns=columns),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "damage_class": st.column_config.SelectboxColumn(
                "damage_class",
                options=[damage_class.name for damage_class in DAMAGE_CLASSES],
                required=True,
            ),
            "confidence": st.column_config.NumberColumn(
                "confidence",
                min_value=0.0,
                max_value=1.0,
                step=0.05,
            ),
            "x": st.column_config.NumberColumn("x", min_value=0.0),
            "y": st.column_config.NumberColumn("y", min_value=0.0),
            "width": st.column_config.NumberColumn("width", min_value=1.0),
            "height": st.column_config.NumberColumn("height", min_value=1.0),
        },
    )

    edited_rows = edited.to_dict("records")
    updated = ImageAnnotations(
        image_path=str(image_path),
        annotations=rows_to_annotations(edited_rows),
        annotator=annotator,
        date_created=image_annotations.date_created,
    )

    if st.button("Save Annotations", type="primary"):
        manager.save_annotations(updated)
        st.success("Annotations saved.")

    render_damage_class_reference()
    return updated
