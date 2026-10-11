import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
<<<<<<< HEAD
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
=======
DATA_PROCESSED_DIR = DATA_DIR / "processed"

# Dataset Paths
MUMBAI_THANE_DATA_PATH = DATA_DIR / "mumbai_thane_traffic_historical.csv"
RAW_DATA_PATH = MUMBAI_THANE_DATA_PATH if MUMBAI_THANE_DATA_PATH.exists() else DATA_DIR / "raw" / "traffic.csv"
PROCESSED_DATA_PATH = DATA_PROCESSED_DIR / "mumbai_thane_features.parquet"
MODEL_PATH = MODELS_DIR / "mumbai_thane_model.joblib"
META_PATH = MODELS_DIR / "mumbai_thane_meta.json"
SAMPLE_LIVE_PATH = DATA_DIR / "sample_live.json"
LIVE_LOG_PATH = DATA_DIR / "live_log.csv"

# Complete 31-node Mumbai & Thane Traffic Network
NODES_CONFIG = {
    "MUM_BKC_01": {
        "name": "BKC Connector / Kalanagar Junction",
        "zone": "BKC Financial District",
        "road_type": "Arterial",
        "lat": 19.0596, "lon": 72.8522, "lanes": 4, "speed_limit": 60, "segment_km": 3.2
    },
    "MUM_BKC_02": {
        "name": "BKC Central Avenue (Diamond Bourse)",
        "zone": "BKC Financial District",
        "road_type": "Arterial",
        "lat": 19.0664, "lon": 72.8660, "lanes": 3, "speed_limit": 50, "segment_km": 2.4
    },
    "MUM_CSMT_01": {
        "name": "CSMT Junction & Fort",
        "zone": "South Mumbai Heritage/Transit",
        "road_type": "Arterial",
        "lat": 18.9402, "lon": 72.8356, "lanes": 3, "speed_limit": 50, "segment_km": 2.8
    },
    "MUM_CSMT_02": {
        "name": "Crawford Market / Marine Lines Connector",
        "zone": "South Mumbai Commercial",
        "road_type": "Arterial",
        "lat": 18.9481, "lon": 72.8342, "lanes": 3, "speed_limit": 40, "segment_km": 2.1
    },
    "MUM_DADAR_01": {
        "name": "Dadar TT Circle (Dr. Ambedkar Road)",
        "zone": "Central Transit Hub",
        "road_type": "Arterial",
        "lat": 19.0178, "lon": 72.8478, "lanes": 3, "speed_limit": 50, "segment_km": 3.0
    },
    "MUM_DADAR_02": {
        "name": "Plaza Cinema / Sena Bhavan (Dadar West)",
        "zone": "Central Commercial",
        "road_type": "Arterial",
        "lat": 19.0222, "lon": 72.8396, "lanes": 2, "speed_limit": 35, "segment_km": 1.8
    },
    "MUM_DADAR_03": {
        "name": "Hindmata Flyover & Junction (Parel)",
        "zone": "Central Choke Point",
        "road_type": "Arterial",
        "lat": 19.0095, "lon": 72.8428, "lanes": 3, "speed_limit": 45, "segment_km": 2.5
    },
    "MUM_EEH_01": {
        "name": "EEH - Chembur Amar Mahal Junction",
        "zone": "Eastern Express Highway",
        "road_type": "Highway",
        "lat": 19.0645, "lon": 72.8990, "lanes": 4, "speed_limit": 75, "segment_km": 4.5
    },
    "MUM_EEH_02": {
        "name": "EEH - Ghatkopar Chhedanagar Interconnect",
        "zone": "Eastern Express Highway",
        "road_type": "Highway",
        "lat": 19.0792, "lon": 72.9081, "lanes": 4, "speed_limit": 75, "segment_km": 4.0
    },
    "MUM_EEH_03": {
        "name": "EEH - Vikhroli Godrej Complex",
        "zone": "Eastern Express Highway",
        "road_type": "Highway",
        "lat": 19.1030, "lon": 72.9262, "lanes": 4, "speed_limit": 75, "segment_km": 4.2
    },
    "MUM_EEH_04": {
        "name": "EEH - Bhandup Pumping Station Junction",
        "zone": "Eastern Express Highway",
        "road_type": "Highway",
        "lat": 19.1444, "lon": 72.9431, "lanes": 4, "speed_limit": 75, "segment_km": 4.8
    },
    "MUM_JVLR_01": {
        "name": "JVLR - Powai Lake / IIT Bombay Junction",
        "zone": "Suburban Cross Link",
        "road_type": "Arterial",
        "lat": 19.1257, "lon": 72.9051, "lanes": 3, "speed_limit": 50, "segment_km": 3.8
    },
    "MUM_LBS_01": {
        "name": "LBS Marg - Mulund West Junction",
        "zone": "Suburban Arterial",
        "road_type": "Arterial",
        "lat": 19.1725, "lon": 72.9472, "lanes": 2, "speed_limit": 40, "segment_km": 3.5
    },
    "MUM_PAREL_04": {
        "name": "Lower Parel / Senapati Bapat Marg",
        "zone": "Commercial IT Corridor",
        "road_type": "Arterial",
        "lat": 18.9953, "lon": 72.8298, "lanes": 3, "speed_limit": 40, "segment_km": 2.6
    },
    "MUM_SION_05": {
        "name": "Sion Circle & Gandhi Market",
        "zone": "Central Interconnect",
        "road_type": "Arterial",
        "lat": 19.0390, "lon": 72.8619, "lanes": 3, "speed_limit": 50, "segment_km": 2.7
    },
    "MUM_SOBO_03": {
        "name": "Marine Drive / Nariman Point Promenade",
        "zone": "South Mumbai Arterial",
        "road_type": "Arterial",
        "lat": 18.9272, "lon": 72.8228, "lanes": 4, "speed_limit": 65, "segment_km": 3.6
    },
    "MUM_SOBO_04": {
        "name": "Haji Ali / Worli Naka",
        "zone": "South-Central Arterial",
        "road_type": "Arterial",
        "lat": 18.9774, "lon": 72.8123, "lanes": 3, "speed_limit": 50, "segment_km": 3.1
    },
    "MUM_TOLL_01": {
        "name": "Mulund Check Naka (Mumbai-Thane Toll Plaza)",
        "zone": "Border Gateway Bottleneck",
        "road_type": "Arterial",
        "lat": 19.1763, "lon": 72.9575, "lanes": 4, "speed_limit": 40, "segment_km": 2.2
    },
    "MUM_WEH_01": {
        "name": "WEH - Santacruz Airport Underpass",
        "zone": "Western Express Highway",
        "road_type": "Highway",
        "lat": 19.0886, "lon": 72.8533, "lanes": 4, "speed_limit": 70, "segment_km": 4.1
    },
    "MUM_WEH_02": {
        "name": "WEH - Andheri Gundavali Flyover",
        "zone": "Western Express Highway",
        "road_type": "Highway",
        "lat": 19.1155, "lon": 72.8567, "lanes": 4, "speed_limit": 70, "segment_km": 4.3
    },
    "MUM_WEH_03": {
        "name": "WEH - Goregaon Hub Mall Junction",
        "zone": "Western Express Highway",
        "road_type": "Highway",
        "lat": 19.1551, "lon": 72.8528, "lanes": 4, "speed_limit": 70, "segment_km": 4.6
    },
    "THN_NODE_01": {
        "name": "Teen Hath Naka (Thane EEH Gateway)",
        "zone": "Thane Core Bottleneck",
        "road_type": "Arterial",
        "lat": 19.1868, "lon": 72.9642, "lanes": 4, "speed_limit": 50, "segment_km": 2.9
    },
    "THN_NODE_02": {
        "name": "Nitin Casting Junction / Panchpakhadi",
        "zone": "Thane Central",
        "road_type": "Arterial",
        "lat": 19.1932, "lon": 72.9667, "lanes": 3, "speed_limit": 45, "segment_km": 2.0
    },
    "THN_NODE_03": {
        "name": "Cadbury Junction (Khopat / Service Road)",
        "zone": "Thane Central",
        "road_type": "Arterial",
        "lat": 19.2015, "lon": 72.9714, "lanes": 3, "speed_limit": 45, "segment_km": 2.3
    },
    "THN_NODE_04": {
        "name": "Majiwada Flyover Junction (Nashik/GB Rd Split)",
        "zone": "Thane Mega Interchange",
        "road_type": "Interchange",
        "lat": 19.2148, "lon": 72.9818, "lanes": 4, "speed_limit": 55, "segment_km": 3.4
    },
    "THN_NODE_05": {
        "name": "Kapurbawdi Circle (Bhiwandi/Ghodbunder Split)",
        "zone": "Thane Commercial Junction",
        "road_type": "Arterial",
        "lat": 19.2230, "lon": 72.9841, "lanes": 3, "speed_limit": 45, "segment_km": 2.1
    },
    "THN_NODE_06": {
        "name": "Manpada - Ghodbunder Road",
        "zone": "Thane Residential Corridor",
        "road_type": "Highway",
        "lat": 19.2435, "lon": 72.9774, "lanes": 3, "speed_limit": 65, "segment_km": 3.7
    },
    "THN_NODE_07": {
        "name": "Waghbil Flyover - Ghodbunder Road",
        "zone": "Thane Express Corridor",
        "road_type": "Highway",
        "lat": 19.2638, "lon": 72.9732, "lanes": 3, "speed_limit": 70, "segment_km": 4.0
    },
    "THN_NODE_08": {
        "name": "Gaimukh Ghat / Fountain Hotel Junction",
        "zone": "Thane Freight Choke Point",
        "road_type": "Ghat/Highway",
        "lat": 19.2933, "lon": 72.9515, "lanes": 2, "speed_limit": 55, "segment_km": 5.2
    },
    "THN_NODE_09": {
        "name": "Thane Railway Station West (Alok Hotel)",
        "zone": "Thane Station Transit Hub",
        "road_type": "Arterial",
        "lat": 19.1872, "lon": 72.9754, "lanes": 2, "speed_limit": 30, "segment_km": 1.5
    },
    "THN_NODE_10": {
        "name": "Kopri Bridge / East Thane Connector",
        "zone": "Thane Railway Bottleneck",
        "road_type": "Bridge",
        "lat": 19.1788, "lon": 72.9702, "lanes": 3, "speed_limit": 40, "segment_km": 2.0
    }
}

# Pre-defined Alternative Route Corridors (For Feature 5: Route Comparison)
ROUTES_CONFIG = {
    "ROUTE_PAIR_1": {
        "name": "Thane to South Mumbai (CSMT)",
        "origin": "Thane Gateway (Teen Hath Naka)",
        "destination": "South Mumbai (CSMT / Fort)",
        "route_a": {
            "name": "Route A (via Eastern Express Highway)",
            "nodes": ["THN_NODE_01", "MUM_TOLL_01", "MUM_EEH_04", "MUM_EEH_03", "MUM_EEH_02", "MUM_EEH_01", "MUM_SION_05", "MUM_DADAR_01", "MUM_CSMT_01"]
        },
        "route_b": {
            "name": "Route B (via LBS Marg & Central Arterial)",
            "nodes": ["THN_NODE_01", "MUM_LBS_01", "MUM_SION_05", "MUM_DADAR_02", "MUM_DADAR_03", "MUM_PAREL_04", "MUM_CSMT_02", "MUM_CSMT_01"]
        }
    },
    "ROUTE_PAIR_2": {
        "name": "Thane to BKC Financial District",
        "origin": "Thane Majiwada Interchange",
        "destination": "BKC Connector / Kalanagar",
        "route_a": {
            "name": "Route A (via EEH & BKC Flyover)",
            "nodes": ["THN_NODE_04", "THN_NODE_01", "MUM_EEH_04", "MUM_EEH_03", "MUM_EEH_02", "MUM_EEH_01", "MUM_BKC_01"]
        },
        "route_b": {
            "name": "Route B (via JVLR & Western Link)",
            "nodes": ["THN_NODE_04", "THN_NODE_01", "MUM_JVLR_01", "MUM_WEH_02", "MUM_WEH_01", "MUM_BKC_01"]
        }
    }
>>>>>>> e809fb07cd44c9b807ba2731379e2fc01fec6502
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

<<<<<<< HEAD
PERCENTILE_CUTOFFS = {
    "Low": 40.0,
    "Moderate": 70.0,
    "High": 90.0
}

=======
>>>>>>> e809fb07cd44c9b807ba2731379e2fc01fec6502
# Forecasting Horizons (minutes)
FORECAST_HORIZONS = [5, 10, 15, 30, 60, 90, 120]
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

<<<<<<< HEAD
=======
# Alert Thresholds
DEFAULT_ALERT_THRESHOLD_DELAY_MIN = 15.0
DEFAULT_ALERT_LEVEL_TRIGGER = "High"  # Triggers for High or Severe

# Color palette for UI
>>>>>>> e809fb07cd44c9b807ba2731379e2fc01fec6502
LEVEL_COLORS = {
    "Low": "#00c853",
    "Moderate": "#ffd600",
    "High": "#ff6d00",
    "Severe": "#d50000"
}

MIN_CALIBRATION_SAMPLES = 20
