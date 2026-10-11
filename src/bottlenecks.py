import datetime
from typing import Dict, Any, List
import pandas as pd
import numpy as np

from src.config import NODES_CONFIG
from src.profile import get_profile_index_at_time
from src.live import load_sample_fallback, speed_ratio_to_level, level_to_midpoint_index
from src.blend import forecast_horizons


def find_network_bottlenecks(
    meta: Dict[str, Any],
    now: datetime.datetime = None,
    live_overrides: Dict[str, float] = None,
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Feature 4: Congestion Bottleneck Finder.
    Automatically identifies and ranks road segments across the network based on
    their current traffic slowdown and predicted congestion deterioration.
    """
    now = now or datetime.datetime.now()
    live_overrides = live_overrides or {}
    
    results = []
    
    for nid, node in NODES_CONFIG.items():
        speed_lim = float(node["speed_limit"])
        lanes = int(node["lanes"])
        
        # Check if live override exists for this node
        if nid in live_overrides:
            curr_spd = float(live_overrides[nid])
        else:
            sample_flow, _ = load_sample_fallback(nid)
            curr_spd = float(sample_flow.get("currentSpeed", speed_lim * 0.5))
            
        curr_ratio = curr_spd / speed_lim
        slowdown_pct = max((1.0 - curr_ratio) * 100.0, 0.0)
        
        # Live congestion index
        live_level = speed_ratio_to_level(curr_ratio)
        live_idx = level_to_midpoint_index(live_level)
        
        # 30-min horizon projection to detect deterioration
        fcasts = forecast_horizons(now, live_index=live_idx, meta=meta, horizons=[15, 30])
        idx_now = fcasts[0]["blended_index"]
        idx_30 = fcasts[1]["blended_index"]
        
        # Predicted deterioration delta (positive if getting worse)
        deterioration_delta = idx_30 - idx_now
        
        # Composite Bottleneck Priority Score (0 to 100)
        # 50% current slowdown ratio, 35% projected congestion at 30 min, 15% rate of deterioration
        score = (
            (0.50 * (slowdown_pct / 100.0)) +
            (0.35 * idx_30) +
            (0.15 * max(deterioration_delta, 0.0))
        ) * 100.0
        score = float(np.clip(score, 0.0, 100.0))
        
        # Estimated queue length in meters
        queue_m = round(max((slowdown_pct / 100.0) * (900.0 / max(lanes, 1)), 0.0))
        
        # Severity Category
        if score >= 70:
            severity = "Critical Choke Point"
            badge_color = "#dc3545"
        elif score >= 45:
            severity = "Active Bottleneck"
            badge_color = "#fd7e14"
        elif score >= 25:
            severity = "Moderate Delay"
            badge_color = "#ffc107"
        else:
            severity = "Free Flowing"
            badge_color = "#28a745"
            
        results.append({
            "node_id": nid,
            "name": node["name"],
            "zone": node["zone"],
            "road_type": node["road_type"],
            "current_speed": round(curr_spd, 1),
            "speed_limit": speed_lim,
            "slowdown_pct": round(slowdown_pct, 1),
            "index_now": round(idx_now, 2),
            "index_30m": round(idx_30, 2),
            "deterioration_delta": round(deterioration_delta, 2),
            "bottleneck_score": round(score, 1),
            "queue_meters": queue_m,
            "severity": severity,
            "badge_color": badge_color
        })
        
    # Rank descending by bottleneck score
    ranked = sorted(results, key=lambda x: x["bottleneck_score"], reverse=True)
    for rank, item in enumerate(ranked, 1):
        item["rank"] = rank
        
    return ranked[:top_n]
