"""Project paths and settings."""

from pathlib import Path
from rasterio.windows import Window


# Repository root, located relative to this file so paths work from any directory.
ROOT = Path(__file__).resolve().parents[1]

RAW_FOLDER = ROOT / "data" / "raw"
INTERIM_FOLDER = ROOT / "data" / "interim"
PROCESSED_FOLDER = ROOT / "data" / "processed"
FIGURES_FOLDER = ROOT / "figures"
DOCS_FOLDER = ROOT / "docs"

# Input files; the names must match the files in data/raw.
NAIP_FILE = RAW_FOLDER / "naip_2021_tile.tif"               
LANDCOVER_FILE = RAW_FOLDER / "landcover_nyc_2021_6in.tif"  
NTA_FILE = RAW_FOLDER / "nta.geojson"                      

# Output files.
ALIGNED_LABELS_FILE = INTERIM_FOLDER / "labels_aligned.tif"
CHIPS_FOLDER = INTERIM_FOLDER / "chips"
PREDICTION_FILE = PROCESSED_FOLDER / "canopy_prediction.tif"
NEIGHBORHOOD_RESULTS_FILE = PROCESSED_FOLDER / "neighborhood_canopy.geojson"
NDVI_PREDICTION_FILE = PROCESSED_FOLDER / "ndvi_prediction.tif"
NDVI_THRESHOLD_FILE = PROCESSED_FOLDER / "ndvi_threshold.json"
MODEL_FILE = ROOT / "canopy_model.joblib"

# Tree canopy is class 1 in the NYC land cover data.
CANOPY_CLASS = 1

# Tile size in pixels (256 pixels is approximately 154 m).
CHIP_SIZE = 256

# Set using the sizing check in notebook 01; no offsets as there is no data border.
STUDY_AREA = Window(col_off=0, row_off=0, width=10013, height=12760)