import os
from pathlib import Path

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

# Predefined Locations
LOCATIONS = {
    "Mumbai": {"lat": 19.0760, "lon": 72.8777, "description": "Financial Capital - High density arterial road"},
    "Pune": {"lat": 18.5204, "lon": 73.8567, "description": "IT & Manufacturing Hub - Urban corridor"},
    "Ratnagiri (Konkan)": {"lat": 16.9902, "lon": 73.3120, "description": "Konkan Coastal Region - Highway / semi-rural road"}
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
# Low: [0.00, 0.40] -> 0.20
# Moderate: [0.40, 0.70] -> 0.55
# High: [0.70, 0.90] -> 0.80
# Severe: [0.90, 1.00] -> 0.95
LEVEL_MIDPOINTS = {
    "Low": 0.20,
    "Moderate": 0.55,
    "High": 0.80,
    "Severe": 0.95
}

# Default volume percentile cutoffs
PERCENTILE_CUTOFFS = {
    "Low": 40.0,
    "Moderate": 70.0,
    "High": 90.0
}

# Forecasting Horizons (minutes)
FORECAST_HORIZONS = [5, 10, 15, 30, 60, 90, 120]

# Decay parameter tau (minutes)
DEFAULT_TAU = 60.0

# Expected weights for tau = 60 min
EXPECTED_WEIGHTS_TAU_60 = {
    5: 0.92,
    10: 0.85,
    15: 0.78,
    30: 0.61,
    60: 0.37,
    90: 0.22,
    120: 0.14
}

# Color palette for UI
LEVEL_COLORS = {
    "Low": "#28a745",        # Green
    "Moderate": "#ffc107",   # Yellow/Amber
    "High": "#fd7e14",       # Orange
    "Severe": "#dc3545"      # Red
}
