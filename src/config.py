import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
RAW_DATA_PATH = DATA_RAW_DIR / "traffic.csv"
PROCESSED_DATA_PATH = DATA_PROCESSED_DIR / "features.parquet"
MODEL_PATH = MODELS_DIR / "model.joblib"
META_PATH = MODELS_DIR / "meta.json"
SAMPLE_LIVE_PATH = BASE_DIR / "data" / "sample_live.json"
LIVE_LOG_PATH = BASE_DIR / "data" / "live_log.csv"
CALIBRATION_JSON_PATH = MODELS_DIR / "calibration.json"
CALIBRATION_REPORT_PATH = BASE_DIR / "data" / "calibration_report.csv"

# API Settings
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")
LOG_INTERVAL_SECONDS = int(os.getenv("LOG_INTERVAL_SECONDS", 300))

# Predefined Locations (from Features 1-2)
LOCATIONS = {
    "Mumbai": {"lat": 19.0760, "lon": 72.8777, "description": "Financial Capital - High density arterial road"},
    "Pune": {"lat": 18.5204, "lon": 73.8567, "description": "IT & Manufacturing Hub - Urban corridor"},
    "Ratnagiri (Konkan)": {"lat": 16.9902, "lon": 73.3120, "description": "Konkan Coastal Region - Highway / semi-rural road"}
}

# 3 Regions, 2 Points per Region (Total 6 points for Feature 3 logger and calibration)
REGIONS = {
    "mumbai": {
        "name": "Mumbai",
        "points": [
            {"point_id": "mum_we_highway", "name": "Western Express Highway (Bandra)", "lat": 19.0596, "lon": 72.8446},
            {"point_id": "mum_ee_highway", "name": "Eastern Express Highway (Chembur)", "lat": 19.0522, "lon": 72.8995}
        ]
    },
    "pune": {
        "name": "Pune",
        "points": [
            {"point_id": "pune_shivajinagar", "name": "Shivajinagar FC Road", "lat": 18.5314, "lon": 73.8446},
            {"point_id": "pune_hinjewadi", "name": "Hinjewadi Phase 1", "lat": 18.5913, "lon": 73.7389}
        ]
    },
    "konkan": {
        "name": "Konkan",
        "points": [
            {"point_id": "konkan_nh66_chiplun", "name": "NH66 Highway (Chiplun Bypass)", "lat": 17.5323, "lon": 73.5178},
            {"point_id": "konkan_nh66_khed", "name": "NH66 Highway (Khed Stretch)", "lat": 17.7214, "lon": 73.3934}
        ]
    }
}

POINTS = {
    p["point_id"]: {**p, "region": reg_key}
    for reg_key, reg in REGIONS.items()
    for p in reg["points"]
}

# Congestion Level Definitions
LEVEL_NAMES = ["Low", "Moderate", "High", "Severe"]

# Live Speed Ratio to Level Mapping (ratio = currentSpeed / freeFlowSpeed)
# > 0.8: Low, 0.6 - 0.8: Moderate, 0.4 - 0.6: High, < 0.4: Severe
SPEED_RATIO_THRESHOLDS = {
    "Low": 0.80,
    "Moderate": 0.60,
    "High": 0.40
}

# Midpoints of the Percentile Bands for common index in [0, 1]
LEVEL_MIDPOINTS = {
    "Low": 0.20,
    "Moderate": 0.55,
    "High": 0.80,
    "Severe": 0.95
}

PERCENTILE_CUTOFFS = {
    "Low": 40.0,
    "Moderate": 70.0,
    "High": 90.0
}

# Forecasting Horizons (minutes)
FORECAST_HORIZONS = [5, 10, 15, 30, 60, 90, 120]

# Decay parameter tau (minutes)
DEFAULT_TAU = 60.0

EXPECTED_WEIGHTS_TAU_60 = {
    5: 0.92,
    10: 0.85,
    15: 0.78,
    30: 0.61,
    60: 0.37,
    90: 0.22,
    120: 0.14
}

LEVEL_COLORS = {
    "Low": "#00c853",
    "Moderate": "#ffd600",
    "High": "#ff6d00",
    "Severe": "#d50000"
}

MIN_CALIBRATION_SAMPLES = 20
