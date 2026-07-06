"""Command-line NASA image downloader for Step 4."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from damage_detection.acquisition.nasa_downloader import NASAImageDownloader


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Download NASA public imagery into the project dataset."
    )
    parser.add_argument("--query", required=True, help="NASA search query.")
    parser.add_argument(
        "--category",
        required=True,
        choices=NASAImageDownloader.allowed_categories,
        help="Dataset category folder under data/raw/.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Maximum number of images to download.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the NASA image download command."""

    args = parse_args()
    downloader = NASAImageDownloader()
    records = downloader.download(
        query=args.query,
        category=args.category,
        limit=args.limit,
    )
    print(f"Downloaded {len(records)} image(s) to data/raw/{args.category}/")
    print("Metadata saved under data/metadata/downloads/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
