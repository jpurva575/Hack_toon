import math
import datetime
from typing import Dict, Any, List
import numpy as np

from src.config import (
    FORECAST_HORIZONS,
    DEFAULT_TAU,
    LEVEL_NAMES
)
from src.profile import get_profile_index_at_time


def compute_decay_weight(h_minutes: float, tau: float = DEFAULT_TAU) -> float:
    """
    Computes exponential decay weight: w(h) = exp(-h / tau).
    """
    return math.exp(-h_minutes / tau)


def index_to_level(index_val: float) -> str:
    """
    Maps blended index in [0, 1] back to congestion level using percentile thresholds:
    Low: < 0.40, Moderate: 0.40 - 0.70, High: 0.70 - 0.90, Severe: > 0.90
    """
    if index_val < 0.40:
        return "Low"
    elif index_val <= 0.70:
        return "Moderate"
    elif index_val <= 0.90:
        return "High"
    else:
        return "Severe"


def forecast_horizons(
    now: datetime.datetime,
    live_index: float,
    meta: Dict[str, Any],
    tau: float = DEFAULT_TAU,
    horizons: List[int] = FORECAST_HORIZONS
) -> List[Dict[str, Any]]:
    """
    Builds the 5 to 120 min short-term forecast by blending historical profile with live reading:
    index(h) = profile(now + h) + (live_index - profile(now)) * w(h)
    where w(h) = exp(-h / tau).
    """
    profile_now = get_profile_index_at_time(now, meta)
    live_deviation = live_index - profile_now
    
    results = []
    for h in horizons:
        future_dt = now + datetime.timedelta(minutes=h)
        prof_future = get_profile_index_at_time(future_dt, meta)
        
        w_live = compute_decay_weight(h, tau)
        w_hist = 1.0 - w_live
        
        # Blended congestion index
        raw_index = prof_future + live_deviation * w_live
        clipped_index = float(np.clip(raw_index, 0.0, 1.0))
        predicted_level = index_to_level(clipped_index)
        
        results.append({
            "horizon_min": h,
            "future_time": future_dt.strftime("%H:%M"),
            "weight_live": round(w_live, 2),
            "weight_history": round(w_hist, 2),
            "weight_live_pct": round(w_live * 100, 1),
            "weight_history_pct": round(w_hist * 100, 1),
            "profile_index": round(prof_future, 4),
            "blended_index": round(clipped_index, 4),
            "predicted_level": predicted_level
        })
        
    return results
