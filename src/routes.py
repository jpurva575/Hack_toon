import datetime
from typing import Dict, Any, List
import pandas as pd

from src.config import NODES_CONFIG, ROUTES_CONFIG
from src.live import load_sample_fallback, speed_ratio_to_level, level_to_midpoint_index
from src.blend import forecast_horizons


def compute_route_metrics(
    route_node_ids: List[str],
    meta: Dict[str, Any],
    now: datetime.datetime = None,
    live_speed_overrides: Dict[str, float] = None
) -> Dict[str, Any]:
    """Computes distance, travel time, delay, and identifies bottleneck for a sequence of nodes."""
    now = now or datetime.datetime.now()
    live_speed_overrides = live_speed_overrides or {}
    
    total_km = 0.0
    free_flow_min = 0.0
    current_time_min = 0.0
    
    # Horizons to evaluate: 15m, 30m, 60m
    horizons_eval = [15, 30, 60]
    future_times_min = {h: 0.0 for h in horizons_eval}
    
    segment_details = []
    worst_node_id = None
    max_slowdown_pct = -1.0
    
    for nid in route_node_ids:
        node = NODES_CONFIG.get(nid, NODES_CONFIG["MUM_BKC_01"])
        seg_km = float(node["segment_km"])
        speed_lim = float(node["speed_limit"])
        
        total_km += seg_km
        seg_free_min = (seg_km / speed_lim) * 60.0
        free_flow_min += seg_free_min
        
        # Current speed
        if nid in live_speed_overrides:
            curr_spd = float(live_speed_overrides[nid])
        else:
            sample_flow, _ = load_sample_fallback(nid)
            curr_spd = float(sample_flow.get("currentSpeed", speed_lim * 0.5))
            
        curr_spd = max(curr_spd, 6.0)
        seg_curr_min = (seg_km / curr_spd) * 60.0
        current_time_min += seg_curr_min
        
        slowdown_pct = max(((speed_lim - curr_spd) / speed_lim) * 100.0, 0.0)
        if slowdown_pct > max_slowdown_pct:
            max_slowdown_pct = slowdown_pct
            worst_node_id = nid
            
        # Horizon speeds via blend
        ratio = curr_spd / speed_lim
        lvl = speed_ratio_to_level(ratio)
        idx_live = level_to_midpoint_index(lvl)
        fcasts = forecast_horizons(now, live_index=idx_live, meta=meta, horizons=horizons_eval)
        
        for f in fcasts:
            h = f["horizon_min"]
            b_idx = f["blended_index"]
            h_spd = max(speed_lim * (1.0 - 0.85 * b_idx), 6.0)
            h_seg_min = (seg_km / h_spd) * 60.0
            future_times_min[h] += h_seg_min
            
        segment_details.append({
            "node_id": nid,
            "name": node["name"],
            "segment_km": seg_km,
            "speed_limit": speed_lim,
            "current_speed": round(curr_spd, 1),
            "slowdown_pct": round(slowdown_pct, 1)
        })
        
    current_delay_min = max(current_time_min - free_flow_min, 0.0)
    avg_speed_kmh = (total_km / (current_time_min / 60.0)) if current_time_min > 0 else 40.0
    worst_node_name = NODES_CONFIG.get(worst_node_id, {}).get("name", "Unknown") if worst_node_id else "None"
    
    return {
        "total_distance_km": round(total_km, 1),
        "free_flow_time_min": round(free_flow_min, 1),
        "current_time_min": round(current_time_min, 1),
        "current_delay_min": round(current_delay_min, 1),
        "average_speed_kmh": round(avg_speed_kmh, 1),
        "time_at_15m": round(future_times_min[15], 1),
        "time_at_30m": round(future_times_min[30], 1),
        "time_at_60m": round(future_times_min[60], 1),
        "worst_bottleneck_node": worst_node_name,
        "worst_slowdown_pct": round(max_slowdown_pct, 1),
        "segment_count": len(route_node_ids),
        "segments": segment_details
    }


def compare_route_pair(
    route_pair_id: str,
    meta: Dict[str, Any],
    now: datetime.datetime = None,
    departure_horizon: int = 0
) -> Dict[str, Any]:
    """Compares Route A and Route B for a selected origin-destination corridor pair."""
    pair_config = ROUTES_CONFIG.get(route_pair_id, ROUTES_CONFIG["ROUTE_PAIR_1"])
    now = now or datetime.datetime.now()
    
    metrics_a = compute_route_metrics(pair_config["route_a"]["nodes"], meta, now)
    metrics_b = compute_route_metrics(pair_config["route_b"]["nodes"], meta, now)
    
    # Travel time for selected departure horizon
    if departure_horizon == 15:
        time_a, time_b = metrics_a["time_at_15m"], metrics_b["time_at_15m"]
    elif departure_horizon == 30:
        time_a, time_b = metrics_a["time_at_30m"], metrics_b["time_at_30m"]
    elif departure_horizon == 60:
        time_a, time_b = metrics_a["time_at_60m"], metrics_b["time_at_60m"]
    else:
        time_a, time_b = metrics_a["current_time_min"], metrics_b["current_time_min"]
        
    delta_min = abs(time_b - time_a)
    
    if delta_min < 1.5:
        recommended = "Either (Equivalent)"
        badge_color = "#6c757d"
        reason = f"Both routes offer virtually identical travel times (~{time_a:.0f} min). Choose based on convenience."
    elif time_a < time_b:
        recommended = pair_config["route_a"]["name"]
        badge_color = "#28a745"
        reason = (
            f"{pair_config['route_a']['name']} is {delta_min:.1f} minutes faster. "
            f"Avoids primary choke point at {metrics_b['worst_bottleneck_node']} on Route B."
        )
    else:
        recommended = pair_config["route_b"]["name"]
        badge_color = "#28a745"
        reason = (
            f"{pair_config['route_b']['name']} is {delta_min:.1f} minutes faster. "
            f"Bypasses severe congestion along {metrics_a['worst_bottleneck_node']} on Route A."
        )
        
    return {
        "corridor_name": pair_config["name"],
        "origin": pair_config["origin"],
        "destination": pair_config["destination"],
        "route_a_name": pair_config["route_a"]["name"],
        "route_b_name": pair_config["route_b"]["name"],
        "metrics_a": metrics_a,
        "metrics_b": metrics_b,
        "selected_horizon_min": departure_horizon,
        "effective_time_a": round(time_a, 1),
        "effective_time_b": round(time_b, 1),
        "time_savings_min": round(delta_min, 1),
        "recommended_route": recommended,
        "badge_color": badge_color,
        "recommendation_reason": reason
    }
