# AI Rocket Damage Detection

An aerospace engineering portfolio project that will use computer vision and deep learning to identify visible rocket or spacecraft surface damage from public imagery.

This repository is being built in 10 steps. Step 5 is now complete: aerospace damage annotation infrastructure for future YOLO training.

## Project Goal

The final system will use Python, OpenCV, PyTorch, NASA public imagery, and a Streamlit interface to support image-based rocket damage detection. Current work is focused only on acquiring, organizing, validating, scoring, downloading, and annotating imagery. No AI model has been built or trained yet.

## Current Status

Step 1 complete:

- Professional repository structure.
- `requirements.txt`.
- Virtual environment instructions.
- Project README.

Step 2 complete:

- Modular dataset manager package.
- Centralized dataset configuration.
- Pluggable data source connectors.
- Image validation and preprocessing utilities.
- JSON and CSV metadata generation.
- Dataset summary report generation.
- Smoke tests for configuration, folders, metadata, and image processing.

Step 3 complete:

- NASA Image and Video Library API client.
- NASA search support for Space Shuttle, Thermal Protection System, Heat Shield, Spacecraft Inspection, Artemis, SLS, and Launch Vehicle imagery.
- Image acquisition pipeline that searches, downloads, stores metadata, validates images, and generates reports.
- Corruption, duplicate, low-resolution, quality, and usefulness scoring.
- JSON report generation for acquisition quality review.
- Tests for NASA client parsing, validation logic, usefulness scoring, and reports.

Step 4 complete:

- Real NASA public API downloader module.
- Command-line NASA image download script.
- Query, category, and limit inputs.
- Image storage in `data/raw/<category>/`.
- Download metadata storage in `data/metadata/downloads/`.
- Duplicate detection using file hashes.
- Corrupted image detection and skipping.
- Tests for image saving, metadata writing, duplicate skipping, corruption skipping, and category validation.

Step 5 complete:

- Central aerospace damage label schema.
- JSON annotation data model.
- Annotation save, load, and validation tools.
- Blank annotation template generator for raw images.
- YOLO label export infrastructure.
- Tests for schema, save/load, validation rejection, and YOLO export.

Do not continue beyond Step 5 until Step 5 has been tested.

## System Architecture

```text
src/damage_detection/dataset/
|-- config.py            # Central paths, formats, image size, limits, and logging settings
|-- data_sources.py      # NASA, public URL collection, and local import source connectors
|-- dataset_manager.py   # Main orchestration layer for ingestion and reporting
|-- image_processor.py   # Validation, resizing, color conversion, normalization, duplicates
`-- metadata_manager.py  # JSON and CSV metadata records

src/damage_detection/acquisition/
|-- image_acquisition.py # High-level NASA acquisition, validation, and report workflow
|-- nasa_client.py       # NASA Image and Video Library API client
|-- nasa_downloader.py   # Real NASA downloader for data/raw/<category> images
|-- dataset_validator.py # Quality checks, duplicate checks, and usefulness scoring
`-- dataset_report.py    # JSON acquisition report generation

src/damage_detection/annotation/
|-- label_schema.py      # Central damage class definitions
|-- annotation_manager.py # JSON annotation save, load, and validation
`-- yolo_export.py       # YOLO label export for future training
```

The design separates responsibilities so future sources can be added without rewriting the whole pipeline. For example, ESA, SpaceX, launch provider image archives, inspection photos, and public aerospace datasets can each become a new `BaseImageSource` connector.

## Folder Structure

```text
AI Rocket Damage Detection/
|-- data/
|   |-- raw/
|   |   |-- Falcon9/
|   |   |-- Starship/
|   |   |-- SLS/
|   |   |-- Artemis/
|   |   |-- Space_Shuttle/
|   |   |-- AtlasV/
|   |   `-- DeltaIV/
|   |-- processed/
|   |-- metadata/
|   `-- logs/
|-- docs/
|-- models/
|-- notebooks/
|-- reports/
|   `-- figures/
|-- scripts/
|-- src/
|   `-- damage_detection/
|       |-- acquisition/
|       |-- annotation/
|       `-- dataset/
|-- scripts/
|   |-- create_annotation_template.py
|   `-- download_nasa_images.py
|-- streamlit_app/
|-- tests/
|-- README.md
`-- requirements.txt
```

The dataset manager automatically creates the required `data/` folders when it starts.

## Installation

Run these commands from the project root.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Usage Examples

Create the dataset folder structure:

```bash
PYTHONPATH=src python -c "from damage_detection.dataset import DatasetManager; DatasetManager(); print('Dataset folders ready')"
```

Import local inspection images into a category:

```python
from pathlib import Path

from damage_detection.dataset import DatasetManager
from damage_detection.dataset.data_sources import LocalImageImportSource

manager = DatasetManager()
source = LocalImageImportSource(Path("path/to/local/images"))
records = manager.ingest_from_source(source, category="Falcon9", limit=10)

print(f"Imported {len(records)} images")
```

Prepare a NASA image connector for later use:

```python
from damage_detection.dataset import DatasetManager
from damage_detection.dataset.data_sources import NASAImagerySource

manager = DatasetManager()
source = NASAImagerySource()
records = manager.ingest_from_source(source, category="Artemis", limit=5)
```

NASA downloads require internet access. The Step 2 tests do not require internet access.

## Step 3 Acquisition Workflow

The Step 3 acquisition workflow is:

1. Search the NASA Image and Video Library API.
2. Normalize NASA metadata.
3. Download selected image previews or assets.
4. Store NASA search metadata locally.
5. Validate downloaded images.
6. Score quality and usefulness for future rocket damage detection.
7. Generate JSON validation and summary reports.

Supported NASA search topics:

- `Space Shuttle`
- `Thermal Protection System`
- `Heat Shield`
- `Spacecraft Inspection`
- `Artemis`
- `SLS`
- `Launch Vehicle`

Quality scoring uses:

- Resolution.
- Aspect ratio.
- File integrity.
- Duplicate penalty.

Usefulness scoring uses simple keyword heuristics:

- High value: close-up inspection imagery, heat shield imagery, tile imagery, spacecraft surface imagery.
- Medium value: rocket body imagery, launch vehicle imagery.
- Low value: distant launch photos and unrelated space imagery.

## Step 3 Usage Examples

Search NASA metadata without downloading images:

```bash
PYTHONPATH=src python -c "from damage_detection.acquisition import NASAImageClient; client = NASAImageClient(); print([record.title for record in client.search('Heat Shield', page_size=3)])"
```

Acquire a small NASA image sample and generate reports:

```bash
PYTHONPATH=src python -c "from damage_detection.acquisition import ImageAcquisitionPipeline; result = ImageAcquisitionPipeline().acquire_nasa_images('Thermal Protection System', limit=3); print(result['report_path'])"
```

Run all standard Step 3 NASA searches:

```python
from damage_detection.acquisition import ImageAcquisitionPipeline

pipeline = ImageAcquisitionPipeline()
results = pipeline.acquire_supported_nasa_searches(limit_per_query=3)

for result in results:
    print(result["query"], result["report_path"])
```

NASA acquisition commands require internet access. The tests use mocked NASA API responses and do not require internet access.

## Step 4 NASA Downloader

Step 4 adds a real downloader for NASA Image and Video Library results. It searches NASA, downloads valid image files, skips duplicates, skips corrupted files, stores images in the selected dataset category, and writes metadata for every saved image.

Supported categories:

- `Falcon9`
- `Starship`
- `SLS`
- `Artemis`
- `Space_Shuttle`
- `DeltaIV`
- `AtlasV`

Run the required Step 4 command:

```bash
python scripts/download_nasa_images.py --query "space shuttle tile inspection" --category Space_Shuttle --limit 25
```

Expected image output:

```text
data/raw/Space_Shuttle/
```

Expected metadata output:

```text
data/metadata/downloads/Space_Shuttle_space_shuttle_tile_inspection_<timestamp>.json
```

Each metadata record contains:

- `filename`
- `NASA title`
- `NASA description`
- `URL`
- `download date`
- `category`

## Step 5 Annotation Workflow

Step 5 adds manual annotation infrastructure for aerospace damage labeling. It prepares the dataset for future YOLO training, but it does not build or train any model.

Damage classes:

```text
0 CRACK
1 TILE_DAMAGE
2 MISSING_TILE
3 SCORCH_MARK
4 DEBRIS_IMPACT
5 INSULATION_DAMAGE
6 ICE_DAMAGE
7 DENT
8 CORROSION
9 OTHER
```

Each class has an ID, name, and description in `src/damage_detection/annotation/label_schema.py`.

Create blank annotation templates for all images under `data/raw/`:

```bash
python scripts/create_annotation_template.py
```

Templates are written to:

```text
data/annotations/json/
```

Each JSON annotation file uses this structure:

```json
{
  "image_path": "data/raw/Space_Shuttle/example.jpg",
  "annotations": [
    {
      "damage_class": "TILE_DAMAGE",
      "confidence": 1.0,
      "bbox": {
        "x": 100,
        "y": 120,
        "width": 80,
        "height": 60
      },
      "notes": "visible tile edge damage"
    }
  ],
  "annotator": "student",
  "date_created": "2026-07-06T00:00:00+00:00"
}
```

Bounding boxes use pixel coordinates:

- `x`: top-left x coordinate.
- `y`: top-left y coordinate.
- `width`: box width in pixels.
- `height`: box height in pixels.

Validation rejects negative coordinates, zero width, zero height, invalid class IDs, and invalid confidence values.

## YOLO Export Format

YOLO labels are exported to:

```text
data/annotations/yolo/images/
data/annotations/yolo/labels/
```

Each YOLO label row uses normalized image coordinates:

```text
class_id center_x center_y width height
```

Example:

```text
1 0.500000 0.500000 0.250000 0.200000
```

This infrastructure is ready for a future training pipeline, where the YOLO image and label folders can be split into train/validation sets. Model creation and training are intentionally deferred to a later step.

## Step 2 Testing

Verify configuration loads:

```bash
PYTHONPATH=src python -c "from damage_detection.dataset.config import DatasetConfig; c = DatasetConfig(); print(c.raw_dir); print(c.image_size)"
```

Verify dataset folders are created:

```bash
PYTHONPATH=src python -c "from damage_detection.dataset import DatasetManager; DatasetManager(); print('Dataset folders created')"
```

Run the Step 2 smoke tests:

```bash
PYTHONPATH=src pytest tests/test_dataset_step2.py
```

Expected result:

```text
4 passed
```

## Step 3 Testing

Run the Step 3 tests:

```bash
PYTHONPATH=src pytest tests/test_acquisition_step3.py
```

Expected result:

```text
4 passed
```

Run Step 2 and Step 3 tests together:

```bash
PYTHONPATH=src pytest tests/test_dataset_step2.py tests/test_acquisition_step3.py
```

Expected result:

```text
8 passed
```

## Step 4 Testing

Run the full test suite:

```bash
PYTHONPATH=src pytest -v
```

Expected result:

```text
12 passed
```

## Step 5 Testing

Run the full test suite:

```bash
PYTHONPATH=src pytest -v
```

Expected result:

```text
16 passed
```

Expected generated folders:

```text
data/raw/Falcon9/
data/raw/Starship/
data/raw/SLS/
data/raw/Artemis/
data/raw/Space_Shuttle/
data/raw/AtlasV/
data/raw/DeltaIV/
data/processed/
data/metadata/
data/logs/
```

Expected generated metadata files after ingestion:

```text
data/metadata/dataset_metadata.json
data/metadata/dataset_metadata.csv
data/metadata/dataset_summary.json
data/logs/dataset_manager.log
```

Expected Step 3 acquisition outputs after a NASA acquisition run:

```text
data/raw/NASA/<query_slug>/
data/metadata/acquisition/nasa_<query_slug>_metadata.json
data/metadata/acquisition/nasa_<query_slug>_validation.json
data/metadata/acquisition/nasa_<query_slug>_report.json
```

The Step 3 report JSON contains:

- Image counts.
- Category counts.
- Average resolution.
- Duplicate count.
- Quality statistics.
- Usefulness statistics.
- Per-image validation results.

Expected Step 4 download outputs:

```text
data/raw/<category>/<downloaded_image_file>
data/metadata/downloads/<category>_<query_slug>_<timestamp>.json
```

Expected Step 5 annotation outputs:

```text
data/annotations/json/<image_stem>.json
data/annotations/yolo/images/<image_file>
data/annotations/yolo/labels/<image_stem>.txt
```

## Future Roadmap

- Step 6: begin dataset curation decisions based on acquisition, download, and annotation reports.
- Add richer annotation review tools for damage labels.
- Add dataset quality reports and visual inspection notebooks.
- Add model training only in a later step.
- Add a Streamlit interface after the core dataset and model pipeline are ready.

## Notes

- The project currently uses PyTorch for future deep learning work.
- TensorFlow can be added later if the project direction changes.
- Large datasets, generated metadata, logs, and trained model files should not be committed directly unless they are small portfolio samples.
