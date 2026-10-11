import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any, List

from src.config import LEVEL_NAMES, NODES_CONFIG

# Core features used by the machine learning model
MODEL_FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "is_weekend",
    "is_holiday_festival",
    "temperature",
    "rainfall_mm",
    "waterlogging_index",
    "air_quality_index",
    "metro_construction_work",
    "vip_movement_or_morcha",
    "vehicle_breakdown_reported",
    "lanes",
    "speed_limit",
    "lag_24h",
    "lag_168h"
]


def load_and_preprocess_mumbai_thane(csv_path: str | Path) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Loads the Mumbai-Thane historical dataset, sorts chronologically per node,
    and computes 24h and 168h volume lags with hour-of-week proxy fallbacks.
    """
    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["node_id", "timestamp"]).reset_index(drop=True)
    
    # Target mapping
    level_map = {"Low": 0, "Moderate": 1, "High": 2, "Severe": 3}
    df["target"] = df["congestion_level"].map(level_map).astype(int)
    
    # Compute per-node lags
    df["lag_24h"] = df.groupby("node_id")["total_vehicle_count"].shift(24)
    df["lag_168h"] = df.groupby("node_id")["total_vehicle_count"].shift(168)
    
    # Hour-of-week mean volume lookup per node as proxy for missing lag values
    how_mean_dict = (
        df.groupby(["node_id", "day_of_week", "hour"])["total_vehicle_count"]
        .mean()
        .to_dict()
    )
    # Serialize keys as string "node_id__dow__hour"
    how_mean_serialized = {
        f"{nid}__{dow}__{hr}": round(float(val), 1)
        for (nid, dow, hr), val in how_mean_dict.items()
    }
    
    # Fill any missing lag (first 24h / 168h of observations) with the hour-of-week mean
    proxy_values = [
        how_mean_dict.get((nid, dow, hr), 1200.0)
        for nid, dow, hr in zip(df["node_id"], df["day_of_week"], df["hour"])
    ]
    df["lag_24h"] = df["lag_24h"].fillna(pd.Series(proxy_values))
    df["lag_168h"] = df["lag_168h"].fillna(pd.Series(proxy_values))
    
    return df, how_mean_serialized


def extract_single_feature_vector(
    node_id: str,
    dt: Any,
    meta: Dict[str, Any],
    weather: Dict[str, float] = None,
    disruptions: Dict[str, int] = None
) -> pd.DataFrame:
    """
    Constructs a 1-row feature DataFrame for inference at an arbitrary datetime
    and node, incorporating weather and local disruption conditions.
    """
    node_info = NODES_CONFIG.get(node_id, NODES_CONFIG["MUM_BKC_01"])
    dow = dt.weekday()
    hr = dt.hour
    is_weekend = 1 if dow >= 5 else 0
    
    weather = weather or {}
    disruptions = disruptions or {}
    
    how_mean = meta.get("how_mean_volume", {})
    dow_prev = (dow - 1) % 7
    lag_24 = how_mean.get(f"{node_id}__{dow_prev}__{hr}", 1200.0)
    lag_168 = how_mean.get(f"{node_id}__{dow}__{hr}", 1200.0)
    
    row = {
        "hour": hr,
        "day_of_week": dow,
        "is_weekend": is_weekend,
        "is_holiday_festival": int(disruptions.get("is_holiday_festival", 0)),
        "temperature": float(weather.get("temperature", 29.0)),
        "rainfall_mm": float(weather.get("rainfall_mm", 0.0)),
        "waterlogging_index": float(disruptions.get("waterlogging_index", 0.0)),
        "air_quality_index": float(weather.get("air_quality_index", 110.0)),
        "metro_construction_work": int(disruptions.get("metro_construction_work", 0)),
        "vip_movement_or_morcha": int(disruptions.get("vip_movement_or_morcha", 0)),
        "vehicle_breakdown_reported": int(disruptions.get("vehicle_breakdown_reported", 0)),
        "lanes": int(node_info["lanes"]),
        "speed_limit": float(node_info["speed_limit"]),
        "lag_24h": float(lag_24),
        "lag_168h": float(lag_168)
    }
    
    return pd.DataFrame([row], columns=MODEL_FEATURE_COLUMNS)


def class_id_to_level(class_id: int) -> str:
    return LEVEL_NAMES[int(class_id)]


def level_to_class_id(level: str) -> int:
    return LEVEL_NAMES.index(level)
