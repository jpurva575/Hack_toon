import datetime
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from src.features import FEATURE_COLUMNS, class_id_to_level


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
    # Group by (day_of_week, hour)
    profile_df = df.groupby(["day_of_week", "hour"])["traffic_volume"].mean().reset_index()
    
    # Calculate min and max volumes for normalized rank/index in [0, 1]
    vol_min = float(df["traffic_volume"].min())
    vol_max = float(df["traffic_volume"].max())
    vol_span = vol_max - vol_min if vol_max > vol_min else 1.0
    
    # 168-hour lookup map
    hourly_profile = {}
    for _, row in profile_df.iterrows():
        dow = int(row["day_of_week"])
        hr = int(row["hour"])
        vol = float(row["traffic_volume"])
        norm_idx = np.clip((vol - vol_min) / vol_span, 0.0, 1.0)
        
        # Level from cutoffs
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
        
    # Weekday curve (Monday=0 to Friday=4)
    weekday_df = df[df["day_of_week"] < 5].groupby("hour")["traffic_volume"].mean()
    weekday_curve = [round(float(weekday_df.get(h, 0.0)), 1) for h in range(24)]
    
    # Weekend curve (Saturday=5 to Sunday=6)
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
    For sub-hour horizons, interpolates linearly between the current hour and the next hour.
    """
    hourly_profile = meta["hourly_profile"]
    dow = dt.weekday()
    hr = dt.hour
    minute = dt.minute
    
    curr_key = f"{dow}_{hr}"
    curr_val = hourly_profile.get(curr_key, {}).get("index", 0.5)
    
    if minute == 0:
        return float(curr_val)
        
    # Next hour key
    dt_next = dt + datetime.timedelta(hours=1)
    next_key = f"{dt_next.weekday()}_{dt_next.hour}"
    next_val = hourly_profile.get(next_key, {}).get("index", curr_val)
    
    fraction = minute / 60.0
    interpolated = (1.0 - fraction) * curr_val + fraction * next_val
    return float(np.clip(interpolated, 0.0, 1.0))


def build_single_row_features(
    dt: datetime.datetime,
    meta: Dict[str, Any],
    weather: Dict[str, float] = None,
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
    # Lag 24h corresponds to same hour, previous day (dow - 1)
    dow_24h = (dow - 1) % 7
    lag_24_val = how_mean.get(f"{dow_24h}_{hr}", 3000.0)
    # Lag 168h corresponds to same day of week, same hour
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
