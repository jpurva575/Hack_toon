from typing import Dict, Any, List


def evaluate_congestion_alerts(
    location_name: str,
    forecasts: List[Dict[str, Any]],
    current_delay_min: float = 0.0,
    delay_threshold_min: float = 12.0,
    alert_level_threshold: str = "High"
) -> Dict[str, Any]:
    """
    Evaluates multi-horizon forecasts against alert thresholds to generate
    proactive congestion warning notifications.
    """
    trigger_levels = ["Severe"] if alert_level_threshold == "Severe" else ["High", "Severe"]
    
    flagged_horizons = []
    for f in forecasts:
        is_level_breach = f["predicted_level"] in trigger_levels
        # Delay proxy: blended_index > 0.70 correlates to High/Severe delay
        is_delay_breach = (f["blended_index"] * 25.0) >= delay_threshold_min
        
        if is_level_breach or is_delay_breach:
            flagged_horizons.append(f)
            
    if not flagged_horizons and current_delay_min < delay_threshold_min:
        return {
            "has_alert": False,
            "severity": "NORMAL",
            "title": "Normal Flow - No Active Congestion Alerts",
            "message": f"Traffic conditions along {location_name} are expected to remain within acceptable limits across all 7 horizons.",
            "earliest_horizon_min": None,
            "peak_horizon_min": None,
            "badge_color": "#28a745"
        }
        
    earliest_h = flagged_horizons[0]["horizon_min"] if flagged_horizons else 0
    # Peak is the horizon with highest blended index
    peak_h_item = max(flagged_horizons, key=lambda x: x["blended_index"]) if flagged_horizons else forecasts[0]
    peak_h = peak_h_item["horizon_min"]
    peak_lvl = peak_h_item["predicted_level"]
    
    if peak_lvl == "Severe" or earliest_h <= 15:
        severity = "CRITICAL"
        badge_color = "#dc3545"
        title = f"🚨 CRITICAL ALERT: Severe Congestion Impending ({location_name})"
        msg = (
            f"Road conditions will deteriorate to {peak_lvl} within +{earliest_h} minutes "
            f"(Peak index: {peak_h_item['blended_index']:.2f} at +{peak_h}m). "
            f"Immediate route diversion recommended to avoid severe gridlock."
        )
    else:
        severity = "WARNING"
        badge_color = "#fd7e14"
        title = f"⚠️ WARNING: Heavy Congestion Predicted ({location_name})"
        msg = (
            f"Predicted traffic volume will reach {peak_lvl} at +{earliest_h} minutes. "
            f"Plan departure window before +{earliest_h}m or budget an additional 15+ minutes travel time."
        )
        
    return {
        "has_alert": True,
        "severity": severity,
        "title": title,
        "message": msg,
        "earliest_horizon_min": earliest_h,
        "peak_horizon_min": peak_h,
        "peak_level": peak_lvl,
        "badge_color": badge_color
    }
