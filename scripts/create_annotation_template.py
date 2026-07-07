"""Create blank JSON annotation templates for images in data/raw/."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from damage_detection.annotation import AnnotationManager, ImageAnnotations
from damage_detection.dataset.config import DatasetConfig


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Create blank annotation templates for all images in data/raw/."
    )
    parser.add_argument(
        "--annotator",
        default="unassigned",
        help="Name or ID of the annotator assigned to the templates.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing annotation template files.",
    )
    return parser.parse_args()


def main() -> int:
    """Generate one blank JSON annotation template per raw image."""

    args = parse_args()
    config = DatasetConfig()
    manager = AnnotationManager(config)
    created = 0
    skipped = 0

    image_paths = sorted(
        path
        for path in config.raw_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in config.supported_image_formats
    )

    for image_path in image_paths:
        output_path = manager.annotation_path_for(image_path)
        if output_path.exists() and not args.overwrite:
            skipped += 1
            continue
        manager.save_annotations(
            ImageAnnotations(
                image_path=str(image_path),
                annotations=[],
                annotator=args.annotator,
            ),
            output_path=output_path,
        )
        created += 1

    print(f"Created {created} annotation template(s)")
    print(f"Skipped {skipped} existing template(s)")
    print("Templates saved under data/annotations/json/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
