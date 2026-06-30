# AI Rocket Damage Detection

An aerospace engineering portfolio project that will use computer vision and deep learning to identify visible rocket or spacecraft surface damage from public imagery.

This repository is being built in 10 steps. Only Step 1 is complete right now: project setup and documentation.

## Project Goal

The final system will use Python, OpenCV, PyTorch, NASA public imagery, and a Streamlit interface to support image-based rocket damage detection. Later steps will add data collection, preprocessing, model training, evaluation, and a web demo.

## Current Status

Step 1 complete:

- Created a professional project folder structure.
- Added `requirements.txt` with starter dependencies.
- Added virtual environment setup instructions.
- Added placeholder files so Git can track empty folders.
- Added this README.

Do not continue to Step 2 until Step 1 has been tested.

## Folder Structure

```text
AI Rocket Damage Detection/
|-- data/
|   |-- raw/
|   |-- processed/
|   `-- annotations/
|-- docs/
|-- models/
|-- notebooks/
|-- reports/
|   `-- figures/
|-- scripts/
|-- src/
|   `-- damage_detection/
|-- streamlit_app/
|-- tests/
|-- README.md
`-- requirements.txt
```

## What Each Folder Is For

- `data/raw/`: original public imagery, such as NASA images, kept unchanged.
- `data/processed/`: cleaned, resized, labeled, or transformed images used for training.
- `data/annotations/`: bounding boxes, masks, labels, or metadata files.
- `docs/`: project notes, research sources, and methodology documentation.
- `models/`: saved model weights and trained checkpoints.
- `notebooks/`: exploratory Jupyter notebooks for visual experiments and data inspection.
- `reports/figures/`: charts, sample outputs, confusion matrices, and portfolio visuals.
- `scripts/`: command-line helper scripts for tasks such as downloading data or preprocessing images.
- `src/damage_detection/`: the main Python package for reusable project code.
- `streamlit_app/`: the future Streamlit web interface.
- `tests/`: automated tests for project code.

## Virtual Environment Setup

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

## How To Test Step 1

After activating the virtual environment and installing dependencies, run:

```bash
python -c "import cv2, torch, streamlit; print('Step 1 setup works')"
```

You should see:

```text
Step 1 setup works
```

## Notes

- The project currently uses PyTorch as the deep learning framework.
- TensorFlow can be added later if the project direction changes.
- Large datasets and trained model files should not be committed directly unless they are small portfolio samples.
