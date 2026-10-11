import math
import datetime
from typing import Dict, Any, List, Optional
import numpy as np

from src.config import (
    FORECAST_HORIZONS,
    DEFAULT_TAU,
    LEVEL_NAMES,
    POINTS
)
from src.profile import get_profile_index_at_time
from src.live import speed_ratio_to_level, level_to_midpoint_index, get_live_data_and_level


def compute_decay_weight(h_minutes: float, tau: float = DEFAULT_TAU) -> float:
    """
    Computes exponential decay weight: w(h) = exp(-h / tau).
    """
    return math.exp(-h_minutes / tau)


def index_to_level(index_val: float) -> str:
    """
    Maps blended index in [0, 1] back to congestion level:
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
    horizons: List[int] = FORECAST_HORIZONS,
    offset: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Builds the 5 to 120 min short-term forecast by blending historical profile with live reading.
    Supports optional calibration offset from Feature 3:
    index(h) = clip(profile(now + h) + offset + (live_index - (profile(now) + offset)) * w(h), 0, 1)
    """
    base_profile_now = get_profile_index_at_time(now, meta)
    profile_now = float(np.clip(base_profile_now + offset, 0.0, 1.0))
    live_deviation = live_index - profile_now
    
    results = []
    for h in horizons:
        future_dt = now + datetime.timedelta(minutes=h)
        base_prof_future = get_profile_index_at_time(future_dt, meta)
        prof_future = float(np.clip(base_prof_future + offset, 0.0, 1.0))
        
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


def forecast(
    point_id: str,
    now_dt: Optional[datetime.datetime] = None,
    offset: float = 0.0,
    simulated_ratio: Optional[float] = None,
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Bridge helper for point-based and dashboard lookups.
    """
    if now_dt is None:
        now_dt = datetime.datetime.now()

    # Load default meta if not passed
    if meta is None:
        import json
        from src.config import META_PATH
        if META_PATH.exists():
            with open(META_PATH, "r") as f:
                meta = json.load(f)
        else:
            meta = {
                "hourly_profile": {
                    f"{dow}_{h}": {"volume": 3000, "index": 0.50, "level": "Moderate"}
                    for dow in range(7) for h in range(24)
                }
            }

    pt_info = POINTS.get(point_id, {"name": point_id, "lat": 19.0596, "lon": 72.8446})
    live_res = get_live_data_and_level(pt_info.get("name", "Mumbai"))
    
    if simulated_ratio is not None:
        cur_ratio = simulated_ratio
        cur_level = speed_ratio_to_level(cur_ratio)
        cur_index = level_to_midpoint_index(cur_level)
    else:
        cur_ratio = live_res["speed_ratio"]
        cur_level = live_res["live_level"]
        cur_index = live_res["live_index"]

    horizons = forecast_horizons(
        now=now_dt,
        live_index=cur_index,
        meta=meta,
        offset=offset
    )

    formatted_horizons = []
    for h in horizons:
        formatted_horizons.append({
            "minutes": h["horizon_min"],
            "target_time": h["future_time"],
            "live_weight": h["weight_live"],
            "history_weight": h["weight_history"],
            "profile_index_calibrated": h["profile_index"],
            "predicted_index": h["blended_index"],
            "predicted_level": h["predicted_level"]
        })

    return {
        "point_id": point_id,
        "name": pt_info.get("name", point_id),
        "region": pt_info.get("region", "mumbai"),
        "current_ratio": cur_ratio,
        "current_level": cur_level,
        "current_index": cur_index,
        "api_ok": live_res.get("traffic_is_live", True),
        "is_simulated": simulated_ratio is not None,
        "offset_applied": offset,
        "horizons": formatted_horizons
    }
