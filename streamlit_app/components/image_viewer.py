"""Image discovery and viewer helpers for the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from PIL import Image

from damage_detection.dataset.config import DatasetConfig


def list_raw_images(config: DatasetConfig) -> list[Path]:
    """Return all supported image files under data/raw/."""

    return sorted(
        path
        for path in config.raw_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in config.supported_image_formats
    )


def image_label(image_path: Path, config: DatasetConfig) -> str:
    """Return a compact display label for an image path."""

    try:
        return str(image_path.relative_to(config.raw_dir))
    except ValueError:
        return image_path.name


def render_image_selector(images: list[Path], config: DatasetConfig) -> Path | None:
    """Render image selection controls and return the selected image path."""

    if not images:
        st.info("No images found under data/raw/. Download NASA images first.")
        return None

    labels = [image_label(path, config) for path in images]
    selected_label = st.selectbox("Image", labels, index=0)
    selected_path = images[labels.index(selected_label)]

    st.image(str(selected_path), caption=selected_label, use_container_width=True)

    with Image.open(selected_path) as image:
        width, height = image.size
    st.caption(f"{width} x {height} px")
    return selected_path


def render_thumbnail_strip(images: list[Path], config: DatasetConfig, limit: int = 8) -> None:
    """Render a small thumbnail strip for quick dataset scanning."""

    if not images:
        return
    st.subheader("Thumbnails")
    columns = st.columns(min(limit, len(images)))
    for column, image_path in zip(columns, images[:limit]):
        with column:
            st.image(str(image_path), caption=image_label(image_path, config), width=120)
