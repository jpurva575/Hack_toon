import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any

from src.config import LEVEL_NAMES, PERCENTILE_CUTOFFS

FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "month",
    "is_weekend",
    "holiday_flag",
    "temp_c",
    "rain_mm",
    "clouds_pct",
    "lag_24h",
    "lag_168h"
]


def clean_raw_data(csv_path: str | Path) -> pd.DataFrame:
    """
    Loads historical traffic CSV, handles duplicates and parses timestamps.
    """
    df = pd.read_csv(csv_path)
    df["date_time"] = pd.to_datetime(df["date_time"])
    # Drop duplicate timestamps, keeping first occurrence
    df = df.drop_duplicates(subset=["date_time"], keep="first").sort_values("date_time")
    return df


def engineer_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Constructs all model features:
    - hour, day_of_week, month, is_weekend, holiday_flag
    - temp_c (Kelvin to Celsius with outlier sanitization)
    - rain_mm (rain_1h with physical capping)
    - clouds_pct (clouds_all clipped [0, 100])
    - lag_24h and lag_168h with hour-of-week average volume fallback for missing timestamps.
    """
    df_indexed = df.set_index("date_time")
    
    # Create complete hourly index to identify missing time steps
    full_idx = pd.date_range(df_indexed.index.min(), df_indexed.index.max(), freq="h")
    df_full = df_indexed.reindex(full_idx)
    
    # Calendar features
    df_full["hour"] = df_full.index.hour
    df_full["day_of_week"] = df_full.index.dayofweek
    df_full["month"] = df_full.index.month
    df_full["is_weekend"] = (df_full["day_of_week"] >= 5).astype(int)
    
    # Holiday flag (1 if known holiday, 0 otherwise)
    if "holiday" in df_full.columns:
        df_full["holiday_flag"] = df_full["holiday"].apply(
            lambda x: 1 if pd.notnull(x) and str(x).strip().lower() != "none" else 0
        )
    else:
        df_full["holiday_flag"] = 0
        
    # Weather features:
    # 1. Temperature: convert Kelvin to Celsius. Clean sensor glitches (e.g., 0 K).
    temp_k = df_full["temp"] if "temp" in df_full.columns else pd.Series(293.15, index=df_full.index)
    temp_c = temp_k - 273.15
    # Replace unrealistic temperatures (< -50 C or > 60 C) with median
    temp_c_valid = temp_c.mask((temp_c < -50) | (temp_c > 60), np.nan)
    median_temp = float(temp_c_valid.median()) if pd.notnull(temp_c_valid.median()) else 15.0
    df_full["temp_c"] = temp_c_valid.fillna(median_temp)
    
    # 2. Rain: rain_1h in mm, capped at 100 mm/h for physical sensor glitches
    rain = df_full["rain_1h"] if "rain_1h" in df_full.columns else pd.Series(0.0, index=df_full.index)
    df_full["rain_mm"] = rain.clip(0.0, 100.0).fillna(0.0)
    
    # 3. Clouds: clouds_all in percentage [0, 100]
    clouds = df_full["clouds_all"] if "clouds_all" in df_full.columns else pd.Series(50.0, index=df_full.index)
    df_full["clouds_pct"] = clouds.clip(0.0, 100.0).fillna(50.0)
    
    # Hour-of-week mean volume lookup (used as proxy for missing lags and future inferences)
    how_mean_volume = (
        df_full.groupby(["day_of_week", "hour"])["traffic_volume"]
        .mean()
        .to_dict()
    )
    # Convert tuple keys to string representation for JSON serialization: "dow_hour"
    how_mean_serialized = {f"{dow}_{h}": float(val) for (dow, h), val in how_mean_volume.items()}
    
    # Lag features
    df_full["lag_24h"] = df_full["traffic_volume"].shift(24)
    df_full["lag_168h"] = df_full["traffic_volume"].shift(168)
    
    # Fill missing lag values with hour-of-week average volume proxy
    lag_proxy = [
        how_mean_volume.get((dow, h), 3000.0)
        for dow, h in zip(df_full["day_of_week"], df_full["hour"])
    ]
    df_full["lag_24h"] = df_full["lag_24h"].fillna(pd.Series(lag_proxy, index=df_full.index))
    df_full["lag_168h"] = df_full["lag_168h"].fillna(pd.Series(lag_proxy, index=df_full.index))
    
    # Filter back to non-null historical traffic records
    clean_df = df_full.dropna(subset=["traffic_volume"]).copy()
    clean_df["date_time"] = clean_df.index
    clean_df = clean_df.reset_index(drop=True)
    
    return clean_df, how_mean_serialized


def compute_volume_cutoffs(volumes: pd.Series) -> Dict[str, float]:
    """
    Computes cutoffs from volume percentiles: Low < P40, Moderate P40-P70, High P70-P90, Severe > P90.
    """
    p40 = float(volumes.quantile(PERCENTILE_CUTOFFS["Low"] / 100.0))
    p70 = float(volumes.quantile(PERCENTILE_CUTOFFS["Moderate"] / 100.0))
    p90 = float(volumes.quantile(PERCENTILE_CUTOFFS["High"] / 100.0))
    return {"P40": p40, "P70": p70, "P90": p90}


def classify_volume_to_level(volume: float, cutoffs: Dict[str, float]) -> str:
    """
    Maps a traffic volume to its percentile-based congestion level.
    """
    if volume < cutoffs["P40"]:
        return "Low"
    elif volume <= cutoffs["P70"]:
        return "Moderate"
    elif volume <= cutoffs["P90"]:
        return "High"
    else:
        return "Severe"


def level_to_class_id(level: str) -> int:
    return LEVEL_NAMES.index(level)


def class_id_to_level(class_id: int) -> str:
    return LEVEL_NAMES[int(class_id)]
