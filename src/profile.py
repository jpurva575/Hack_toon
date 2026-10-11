import os
import json
import datetime
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
<<<<<<< HEAD

from src.features import FEATURE_COLUMNS, class_id_to_level
from src.config import META_PATH
=======
from typing import Dict, Any, List, Tuple
from src.features import extract_single_feature_vector, class_id_to_level
>>>>>>> e809fb07cd44c9b807ba2731379e2fc01fec6502


def build_network_profiles(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes per-node and global 168-hour profiles, plus weekday vs weekend curves.
    """
<<<<<<< HEAD
    profile_df = df.groupby(["day_of_week", "hour"])["traffic_volume"].mean().reset_index()
    vol_min = float(df["traffic_volume"].min())
    vol_max = float(df["traffic_volume"].max())
    vol_span = vol_max - vol_min if vol_max > vol_min else 1.0
    
    hourly_profile = {}
    for _, row in profile_df.iterrows():
        dow = int(row["day_of_week"])
        hr = int(row["hour"])
        vol = float(row["traffic_volume"])
        norm_idx = np.clip((vol - vol_min) / vol_span, 0.0, 1.0)
        
        if vol < cutoffs["P40"]:
            lvl = "Low"
        elif vol <= cutoffs["P70"]:
            lvl = "Moderate"
        elif vol <= cutoffs["P90"]:
            lvl = "High"
        else:
            lvl = "Severe"
            
        hourly_profile[f"{dow}_{hr}"] = {
            "volume": round(vol, 1),
            "index": round(float(norm_idx), 4),
            "level": lvl
        }
        
    weekday_df = df[df["day_of_week"] < 5].groupby("hour")["traffic_volume"].mean()
    weekday_curve = [round(float(weekday_df.get(h, 0.0)), 1) for h in range(24)]
    
    weekend_df = df[df["day_of_week"] >= 5].groupby("hour")["traffic_volume"].mean()
    weekend_curve = [round(float(weekend_df.get(h, 0.0)), 1) for h in range(24)]
=======
    profiles = {}
    
    # 1. Global network-level profile across all nodes
    global_df = df.groupby(["day_of_week", "hour"])[["total_vehicle_count", "average_speed_kmh", "congestion_score"]].mean().reset_index()
    global_profile = {}
    for _, r in global_df.iterrows():
        dow = int(r["day_of_week"])
        hr = int(r["hour"])
        score = float(r["congestion_score"])
        norm_idx = np.clip(score / 100.0, 0.0, 1.0)
        global_profile[f"{dow}_{hr}"] = {
            "volume": round(float(r["total_vehicle_count"]), 1),
            "speed": round(float(r["average_speed_kmh"]), 1),
            "score": round(score, 1),
            "index": round(float(norm_idx), 4)
        }
    profiles["global_profile"] = global_profile
    
    # 2. Per-node profiles
    node_profiles = {}
    for nid, group in df.groupby("node_id"):
        n_prof = group.groupby(["day_of_week", "hour"])[["total_vehicle_count", "average_speed_kmh", "congestion_score"]].mean().reset_index()
        n_dict = {}
        for _, r in n_prof.iterrows():
            dow = int(r["day_of_week"])
            hr = int(r["hour"])
            score = float(r["congestion_score"])
            norm_idx = np.clip(score / 100.0, 0.0, 1.0)
            n_dict[f"{dow}_{hr}"] = {
                "volume": round(float(r["total_vehicle_count"]), 1),
                "speed": round(float(r["average_speed_kmh"]), 1),
                "score": round(score, 1),
                "index": round(float(norm_idx), 4)
            }
        node_profiles[nid] = n_dict
    profiles["node_profiles"] = node_profiles
>>>>>>> e809fb07cd44c9b807ba2731379e2fc01fec6502
    
    # 3. Weekday vs Weekend Volume Curves (Network Average)
    weekday_df = df[df["day_of_week"] < 5].groupby("hour")["total_vehicle_count"].mean()
    weekend_df = df[df["day_of_week"] >= 5].groupby("hour")["total_vehicle_count"].mean()
    profiles["weekday_curve"] = [round(float(weekday_df.get(h, 0.0)), 1) for h in range(24)]
    profiles["weekend_curve"] = [round(float(weekend_df.get(h, 0.0)), 1) for h in range(24)]
    
    return profiles


def get_profile_index_at_time(
    dt: datetime.datetime,
    meta: Dict[str, Any],
    node_id: str = None
) -> float:
    """
<<<<<<< HEAD
    Calculates profile_index(t) in [0, 1].
    For sub-hour horizons, interpolates linearly between current hour and next hour.
    """
    hourly_profile = meta.get("hourly_profile", {})
=======
    Retrieves historical congestion profile index [0, 1] for a timestamp and optional node.
    Linearly interpolates across sub-hour minutes.
    """
    node_profiles = meta.get("node_profiles", {})
    if node_id and node_id in node_profiles:
        profile_map = node_profiles[node_id]
    else:
        profile_map = meta.get("global_profile", meta.get("hourly_profile", {}))
        
>>>>>>> e809fb07cd44c9b807ba2731379e2fc01fec6502
    dow = dt.weekday()
    hr = dt.hour
    minute = dt.minute
    
    curr_key = f"{dow}_{hr}"
    curr_item = profile_map.get(curr_key, {})
    curr_val = curr_item.get("index", 0.40)
    
    if minute == 0:
        return float(curr_val)
        
    dt_next = dt + datetime.timedelta(hours=1)
    next_key = f"{dt_next.weekday()}_{dt_next.hour}"
    next_item = profile_map.get(next_key, {})
    next_val = next_item.get("index", curr_val)
    
    fraction = minute / 60.0
    interpolated = (1.0 - fraction) * curr_val + fraction * next_val
    return float(np.clip(interpolated, 0.0, 1.0))


<<<<<<< HEAD
def predict_profile(dt: datetime.datetime, weather: Optional[Dict[str, float]] = None) -> float:
    """
    Bridge function: Loads meta.json and evaluates get_profile_index_at_time(dt, meta).
    Provides seamless compatibility across Feature 1, Feature 3, and pan-India routing.
    """
    if META_PATH.exists():
        try:
            with open(META_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
                return get_profile_index_at_time(dt, meta)
        except Exception:
            pass

    # Sinusoidal diurnal fallback if meta.json is absent
    hour = dt.hour + dt.minute / 60.0
    is_weekend = dt.weekday() >= 5
    if is_weekend:
        val = 0.25 + 0.35 * np.exp(-((hour - 16.0) ** 2) / 18.0)
    else:
        morning = 0.50 * np.exp(-((hour - 9.5) ** 2) / 4.0)
        evening = 0.60 * np.exp(-((hour - 18.5) ** 2) / 6.0)
        val = 0.20 + morning + evening

    return float(np.clip(round(val, 4), 0.0, 1.0))


def build_single_row_features(
=======
def predict_node_level(
    node_id: str,
>>>>>>> e809fb07cd44c9b807ba2731379e2fc01fec6502
    dt: datetime.datetime,
    model: Any,
    meta: Dict[str, Any],
<<<<<<< HEAD
    weather: Optional[Dict[str, float]] = None,
    holiday_flag: int = 0
) -> pd.DataFrame:
=======
    weather: Dict[str, float] = None,
    disruptions: Dict[str, int] = None
) -> Tuple[str, List[float], pd.DataFrame]:
>>>>>>> e809fb07cd44c9b807ba2731379e2fc01fec6502
    """
    Predicts congestion level (Low, Moderate, High, Severe) and class probabilities for a node.
    """
<<<<<<< HEAD
    if weather is None:
        weather = {"temp_c": 25.0, "rain_mm": 0.0, "clouds_pct": 30.0}
        
    dow = dt.weekday()
    hr = dt.hour
    month = dt.month
    is_weekend = 1 if dow >= 5 else 0
    
    how_mean = meta.get("how_mean_volume", {})
    dow_24h = (dow - 1) % 7
    lag_24_val = how_mean.get(f"{dow_24h}_{hr}", 3000.0)
    lag_168_val = how_mean.get(f"{dow}_{hr}", 3000.0)
    
    row_data = {
        "hour": hr,
        "day_of_week": dow,
        "month": month,
        "is_weekend": is_weekend,
        "holiday_flag": holiday_flag,
        "temp_c": weather.get("temp_c", 25.0),
        "rain_mm": weather.get("rain_mm", 0.0),
        "clouds_pct": weather.get("clouds_pct", 30.0),
        "lag_24h": float(lag_24_val),
        "lag_168h": float(lag_168_val)
    }
    
    return pd.DataFrame([row_data], columns=FEATURE_COLUMNS)
=======
    X_single = extract_single_feature_vector(node_id, dt, meta, weather, disruptions)
    pred_class_id = int(model.predict(X_single)[0])
    pred_probs = model.predict_proba(X_single)[0]
    return class_id_to_level(pred_class_id), [float(p) for p in pred_probs], X_single
>>>>>>> e809fb07cd44c9b807ba2731379e2fc01fec6502
