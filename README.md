# AI Rocket Damage Detection

An aerospace engineering portfolio project that will use computer vision and deep learning to identify visible rocket or spacecraft surface damage from public imagery.

This repository is being built in 10 steps. Step 2 is now complete: aerospace image ingestion and dataset management.

## Project Goal

The final system will use Python, OpenCV, PyTorch, NASA public imagery, and a Streamlit interface to support image-based rocket damage detection. Current work is focused only on dataset organization, validation, preprocessing, and metadata. No AI model has been built or trained yet.

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

Do not continue to Step 3 until Step 2 has been tested.

## System Architecture

```text
src/damage_detection/dataset/
|-- config.py            # Central paths, formats, image size, limits, and logging settings
|-- data_sources.py      # NASA, public URL collection, and local import source connectors
|-- dataset_manager.py   # Main orchestration layer for ingestion and reporting
|-- image_processor.py   # Validation, resizing, color conversion, normalization, duplicates
`-- metadata_manager.py  # JSON and CSV metadata records
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
|       `-- dataset/
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

## Future Roadmap

- Step 3: collect and organize initial NASA/public aerospace imagery.
- Add richer annotation support for damage labels.
- Add dataset quality reports and visual inspection notebooks.
- Add model training only in a later step.
- Add a Streamlit interface after the core dataset and model pipeline are ready.

## Notes

- The project currently uses PyTorch for future deep learning work.
- TensorFlow can be added later if the project direction changes.
- Large datasets, generated metadata, logs, and trained model files should not be committed directly unless they are small portfolio samples.
