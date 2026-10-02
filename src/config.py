"""Project paths and settings."""
from pathlib import Path
from rasterio.windows import Window

# Repository root, located relative to this file so paths work from any directory.
ROOT = Path(__file__).resolve().parents[1]
RAW, INTERIM, PROCESSED = ROOT / "data/raw", ROOT / "data/interim", ROOT / "data/processed"
FIGURES, DOCS = ROOT / "figures", ROOT / "docs"

# Input files; the names must match the files in data/raw.
NAIP_FILE = RAW / "naip_2021_tile.tif"
LANDCOVER_FILE = RAW / "landcover_nyc_2021_6in.tif"
NTA_FILE = RAW / "nta.geojson"

# Output files.
LABELS_FILE = INTERIM / "labels_aligned.tif"
CHIPS_FOLDER = INTERIM / "chips"
RF_PREDICTION_FILE = PROCESSED / "rf_prediction.tif"
NDVI_PREDICTION_FILE = PROCESSED / "ndvi_prediction.tif"
NDVI_THRESHOLD_FILE = PROCESSED / "ndvi_threshold.json"
NEIGHBORHOOD_FILE = PROCESSED / "neighborhood_canopy.geojson"
MODEL_FILE = ROOT / "canopy_model.joblib"

# Land cover classes used in the analysis.
CANOPY_CLASS, GRASS_CLASS, BUILDING_CLASS = 1, 2, 5
CLASS_NAMES = {1: "tree canopy", 2: "grass/shrub", 3: "bare ground", 4: "water",
               5: "building", 6: "road", 7: "other paved", 8: "railroad"}

# Tile size in pixels (256 pixels is approximately 154 m).
CHIP_SIZE = 256

# Set using the sizing check in notebook 01; offsets exclude the nodata border.
STUDY_AREA = Window(col_off=0, row_off=0, width=10013, height=12760)