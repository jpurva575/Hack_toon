from typing import Dict, Any, List
from src.config import NODES_CONFIG


def estimate_segment_delay(
    node_id: str,
    current_speed: float,
    forecasts: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Feature 3: Traffic Impact and Delay Estimator.
    Quantifies the additional travel time caused by congestion by comparing free-flow
    travel time with current and predicted travel time for a selected road segment.
    """
    node_info = NODES_CONFIG.get(node_id, NODES_CONFIG["MUM_BKC_01"])
    segment_km = float(node_info["segment_km"])
    speed_limit = float(node_info["speed_limit"])
    
    # 1. Baseline Free-Flow Calculations
    free_flow_time_min = (segment_km / speed_limit) * 60.0
    
    # 2. Current Observation Calculations
    effective_current_speed = max(float(current_speed), 5.0)
    current_time_min = (segment_km / effective_current_speed) * 60.0
    current_delay_min = max(current_time_min - free_flow_time_min, 0.0)
    current_tti = current_time_min / free_flow_time_min if free_flow_time_min > 0 else 1.0
    speed_drop_pct = max(((speed_limit - effective_current_speed) / speed_limit) * 100.0, 0.0)
    
    # 3. Horizon Projections (if forecasts provided)
    horizon_delays = []
    if forecasts:
        for f in forecasts:
            h = f["horizon_min"]
            b_idx = f["blended_index"]
            # Map congestion index [0, 1] to estimated road speed
            # b_idx = 0.0 -> full speed_limit
            # b_idx = 1.0 -> severe slowdown (~15% of speed limit or 6 km/h floor)
            h_speed = max(speed_limit * (1.0 - 0.85 * b_idx), 6.0)
            h_time = (segment_km / h_speed) * 60.0
            h_delay = max(h_time - free_flow_time_min, 0.0)
            h_tti = h_time / free_flow_time_min
            
            horizon_delays.append({
                "horizon_min": h,
                "future_time": f.get("future_time", f"+{h}m"),
                "predicted_level": f.get("predicted_level", "Unknown"),
                "blended_index": round(b_idx, 2),
                "speed_kmh": round(h_speed, 1),
                "travel_time_min": round(h_time, 1),
                "delay_min": round(h_delay, 1),
                "tti": round(h_tti, 2)
            })
            
    # Commuter travel advice
    if current_delay_min < 2.0:
        advice = "Green Corridor: Traffic is flowing near free-flow speed. Best time to travel."
    elif current_delay_min < 8.0:
        advice = "Moderate Slowdown: Expect minor signal queues and intersection braking."
    elif current_delay_min < 18.0:
        advice = "High Delay: Consider deferring departure by 30-45 min or taking an alternate route."
    else:
        advice = "Severe Congestion: Road operating at breakdown capacity. Avoid if possible."

    return {
        "node_id": node_id,
        "name": node_info["name"],
        "segment_km": segment_km,
        "speed_limit": speed_limit,
        "current_speed": round(effective_current_speed, 1),
        "free_flow_time_min": round(free_flow_time_min, 1),
        "current_time_min": round(current_time_min, 1),
        "current_delay_min": round(current_delay_min, 1),
        "speed_drop_pct": round(speed_drop_pct, 1),
        "current_tti": round(current_tti, 2),
        "horizon_delays": horizon_delays,
        "advice": advice
    }
