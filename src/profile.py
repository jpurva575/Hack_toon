import datetime
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from src.features import extract_single_feature_vector, class_id_to_level


def build_network_profiles(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes per-node and global 168-hour profiles, plus weekday vs weekend curves.
    """
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
    Retrieves historical congestion profile index [0, 1] for a timestamp and optional node.
    Linearly interpolates across sub-hour minutes.
    """
    node_profiles = meta.get("node_profiles", {})
    if node_id and node_id in node_profiles:
        profile_map = node_profiles[node_id]
    else:
        profile_map = meta.get("global_profile", meta.get("hourly_profile", {}))
        
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


def predict_node_level(
    node_id: str,
    dt: datetime.datetime,
    model: Any,
    meta: Dict[str, Any],
    weather: Dict[str, float] = None,
    disruptions: Dict[str, int] = None
) -> Tuple[str, List[float], pd.DataFrame]:
    """
    Predicts congestion level (Low, Moderate, High, Severe) and class probabilities for a node.
    """
    X_single = extract_single_feature_vector(node_id, dt, meta, weather, disruptions)
    pred_class_id = int(model.predict(X_single)[0])
    pred_probs = model.predict_proba(X_single)[0]
    return class_id_to_level(pred_class_id), [float(p) for p in pred_probs], X_single
