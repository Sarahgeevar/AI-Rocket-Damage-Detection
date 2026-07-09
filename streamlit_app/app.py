"""Streamlit dashboard for NASA aerospace image review and annotations."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from damage_detection.annotation import AnnotationManager, YOLOExporter
from damage_detection.dataset.config import DatasetConfig
from streamlit_app.components.annotation_panel import render_annotation_panel
from streamlit_app.components.dataset_stats import (
    annotation_files_with_existing_images,
    compute_dataset_stats,
    render_dataset_stats,
)
from streamlit_app.components.image_viewer import (
    list_raw_images,
    render_image_selector,
    render_thumbnail_strip,
)


def main() -> None:
    """Run the Step 6 annotation review dashboard."""

    st.set_page_config(
        page_title="AI Rocket Damage Detection",
        layout="wide",
    )
    st.title("AI Rocket Damage Detection")
    st.caption("Step 6: NASA image review and annotation management")

    config = DatasetConfig(project_root=PROJECT_ROOT)
    manager = AnnotationManager(config)
    exporter = YOLOExporter(config, manager)
    images = list_raw_images(config)

    with st.sidebar:
        st.header("Controls")
        annotator = st.text_input("Annotator", value="student")
        stats = compute_dataset_stats(config, manager)
        render_dataset_stats(stats)

        if st.button("Export YOLO Dataset"):
            annotation_paths = annotation_files_with_existing_images(manager)
            exported = exporter.export_to_yolo(annotation_paths)
            st.success(f"Exported {len(exported)} YOLO label file(s).")

    left, right = st.columns([1.25, 1])
    with left:
        selected_image = render_image_selector(images, config)
        render_thumbnail_strip(images, config)

    with right:
        if selected_image is not None:
            render_annotation_panel(manager, selected_image, annotator)


if __name__ == "__main__":
    main()
