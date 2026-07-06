"""Central configuration for aerospace image dataset management."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class DatasetConfig:
    """Configuration values used by the dataset ingestion pipeline.

    All paths are centralized here so future project steps can change storage
    locations, image dimensions, and metadata outputs without editing pipeline
    logic.
    """

    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[3]
    )
    raw_categories: tuple[str, ...] = (
        "Falcon9",
        "Starship",
        "SLS",
        "Artemis",
        "Space_Shuttle",
        "AtlasV",
        "DeltaIV",
    )
    image_size: tuple[int, int] = (224, 224)
    supported_image_formats: tuple[str, ...] = (
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    )
    max_downloads_per_source: int = 25
    duplicate_hash_size: int = 16
    log_level: str = "INFO"
    log_filename: str = "dataset_manager.log"
    metadata_json_filename: str = "dataset_metadata.json"
    metadata_csv_filename: str = "dataset_metadata.csv"
    summary_json_filename: str = "dataset_summary.json"

    @property
    def data_dir(self) -> Path:
        """Return the root data directory."""

        return self.project_root / "data"

    @property
    def raw_dir(self) -> Path:
        """Return the raw imagery directory."""

        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        """Return the processed imagery directory."""

        return self.data_dir / "processed"

    @property
    def metadata_dir(self) -> Path:
        """Return the metadata output directory."""

        return self.data_dir / "metadata"

    @property
    def logs_dir(self) -> Path:
        """Return the logging directory."""

        return self.data_dir / "logs"

    @property
    def log_path(self) -> Path:
        """Return the dataset manager log file path."""

        return self.logs_dir / self.log_filename

    @property
    def metadata_json_path(self) -> Path:
        """Return the JSON metadata file path."""

        return self.metadata_dir / self.metadata_json_filename

    @property
    def metadata_csv_path(self) -> Path:
        """Return the CSV metadata file path."""

        return self.metadata_dir / self.metadata_csv_filename

    @property
    def summary_json_path(self) -> Path:
        """Return the dataset summary report path."""

        return self.metadata_dir / self.summary_json_filename
