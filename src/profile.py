import os
import json
import datetime
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

from src.features import FEATURE_COLUMNS, class_id_to_level
from src.config import META_PATH


def build_hourly_profile_and_curves(
    df: pd.DataFrame,
    cutoffs: Dict[str, float]
) -> Dict[str, Any]:
    """
    Computes:
    1. Hourly profile for all 168 hours of the week (day_of_week 0..6, hour 0..23).
    2. Weekday vs weekend average 24-hour volume curves.
    3. Min/Max historical volume for percentile rank normalization.
    """
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
    
    return {
        "hourly_profile": hourly_profile,
        "weekday_curve": weekday_curve,
        "weekend_curve": weekend_curve,
        "vol_min": vol_min,
        "vol_max": vol_max
    }


def get_profile_index_at_time(
    dt: datetime.datetime,
    meta: Dict[str, Any]
) -> float:
    """
    Calculates profile_index(t) in [0, 1].
    For sub-hour horizons, interpolates linearly between current hour and next hour.
    """
    hourly_profile = meta.get("hourly_profile", {})
    dow = dt.weekday()
    hr = dt.hour
    minute = dt.minute
    
    curr_key = f"{dow}_{hr}"
    curr_val = hourly_profile.get(curr_key, {}).get("index", 0.5)
    
    if minute == 0:
        return float(curr_val)
        
    dt_next = dt + datetime.timedelta(hours=1)
    next_key = f"{dt_next.weekday()}_{dt_next.hour}"
    next_val = hourly_profile.get(next_key, {}).get("index", curr_val)
    
    fraction = minute / 60.0
    interpolated = (1.0 - fraction) * curr_val + fraction * next_val
    return float(np.clip(interpolated, 0.0, 1.0))


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
    dt: datetime.datetime,
    meta: Dict[str, Any],
    weather: Optional[Dict[str, float]] = None,
    holiday_flag: int = 0
) -> pd.DataFrame:
    """
    Constructs a 1-row DataFrame of features for any datetime.
    Lag proxy: Uses hour-of-week average volume for lag_24h and lag_168h.
    """
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
