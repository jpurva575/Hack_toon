import os
import json
import logging
from typing import Dict, Any, Tuple
import requests
from dotenv import load_dotenv

from src.config import (
<<<<<<< HEAD
    LOCATIONS,
    POINTS,
=======
    NODES_CONFIG,
>>>>>>> e809fb07cd44c9b807ba2731379e2fc01fec6502
    SPEED_RATIO_THRESHOLDS,
    LEVEL_MIDPOINTS,
    SAMPLE_LIVE_PATH
)

load_dotenv()
logging.basicConfig(level=logging.INFO)


def resolve_node_info(location_query: str) -> Tuple[str, Dict[str, Any]]:
    """Resolves node_id and metadata from either a node_id or location/name string."""
    if location_query in NODES_CONFIG:
        return location_query, NODES_CONFIG[location_query]
        
    # Search by name or substring
    for nid, info in NODES_CONFIG.items():
        if location_query.lower() in info["name"].lower() or info["name"].lower() in location_query.lower():
            return nid, info
            
    # Default fallback
    return "MUM_BKC_01", NODES_CONFIG["MUM_BKC_01"]


def load_sample_fallback(node_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Loads saved sample live response from data/sample_live.json when offline or API key absent."""
    if SAMPLE_LIVE_PATH.exists():
        with open(SAMPLE_LIVE_PATH, "r") as f:
            data = json.load(f)
<<<<<<< HEAD
        if location_name in data:
            loc_data = data[location_name]
            return loc_data.get("flowSegmentData", loc_data), loc_data.get("weather", {})
            
=======
        if node_id in data:
            entry = data[node_id]
            return entry.get("flowSegmentData", {}), entry.get("weather", {})
            
    # Standard default fallback
    node_info = NODES_CONFIG.get(node_id, NODES_CONFIG["MUM_BKC_01"])
    speed_limit = node_info["speed_limit"]
    curr_speed = round(speed_limit * 0.50, 1)
    
>>>>>>> e809fb07cd44c9b807ba2731379e2fc01fec6502
    fallback_flow = {
        "currentSpeed": curr_speed,
        "freeFlowSpeed": speed_limit,
        "currentTravelTime": int((node_info["segment_km"] / curr_speed) * 3600),
        "freeFlowTravelTime": int((node_info["segment_km"] / speed_limit) * 3600),
        "confidence": 0.90
    }
    fallback_weather = {
        "temperature_2m": 29.5,
        "precipitation": 0.0,
        "cloud_cover": 40
    }
    return fallback_flow, fallback_weather


def fetch_tomtom_traffic(lat: float, lon: float, api_key: str = None) -> Tuple[Dict[str, Any], bool, str]:
    """Calls TomTom Flow Segment API if key is present."""
    key = api_key or os.getenv("TOMTOM_API_KEY")
    if not key or key.strip() == "":
        return {}, False, "No TomTom API key set. Using verified local road benchmark."
        
    url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
    params = {"point": f"{lat},{lon}", "key": key}
    
    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            flow_data = data.get("flowSegmentData", {})
            if "currentSpeed" in flow_data and "freeFlowSpeed" in flow_data:
                return flow_data, True, "Live TomTom Traffic API stream connected"
            else:
                return {}, False, "TomTom response missing speed fields"
        else:
            return {}, False, f"TomTom HTTP status {resp.status_code}"
    except Exception as e:
        return {}, False, f"TomTom API connection error: {str(e)}"


def fetch_open_meteo_weather(lat: float, lon: float) -> Tuple[Dict[str, Any], bool, str]:
    """Calls Open-Meteo free weather endpoint."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,precipitation,cloud_cover"
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            current = resp.json().get("current", {})
            return {
                "temperature_2m": current.get("temperature_2m", 29.0),
                "precipitation": current.get("precipitation", 0.0),
                "cloud_cover": current.get("cloud_cover", 35)
            }, True, "Live Open-Meteo Weather connected"
        else:
            return {}, False, f"Open-Meteo HTTP {resp.status_code}"
    except Exception as e:
        return {}, False, f"Open-Meteo connection error: {str(e)}"


def speed_ratio_to_level(ratio: float) -> str:
    """
    Maps speed ratio = currentSpeed / freeFlowSpeed to congestion level:
    > 0.8: Low, 0.6 - 0.8: Moderate, 0.4 - 0.6: High, < 0.4: Severe
    """
    if ratio > SPEED_RATIO_THRESHOLDS["Low"]:
        return "Low"
    elif ratio >= SPEED_RATIO_THRESHOLDS["Moderate"]:
        return "Moderate"
    elif ratio >= SPEED_RATIO_THRESHOLDS["High"]:
        return "High"
    else:
        return "Severe"


def level_to_midpoint_index(level: str) -> float:
    """Converts level to midpoint index in [0, 1]."""
    return LEVEL_MIDPOINTS.get(level, 0.55)


def get_live_data_and_level(
    location_query: str,
    api_key: str = None
) -> Dict[str, Any]:
<<<<<<< HEAD
    """
    Orchestrates live traffic and weather retrieval with fallback.
    Computes speed ratio, live congestion level, and live midpoint index.
    """
    if location_name in LOCATIONS:
        loc = LOCATIONS[location_name]
    elif location_name in POINTS:
        loc = POINTS[location_name]
    else:
        loc = LOCATIONS["Mumbai"]
        
    lat, lon = loc["lat"], loc["lon"]
    
    flow_data, traffic_is_live, traffic_msg = fetch_tomtom_traffic(lat, lon, api_key)
    weather_data, weather_is_live, weather_msg = fetch_open_meteo_weather(lat, lon)
    sample_flow, sample_weather = load_sample_fallback(location_name)
    
=======
    """Fetches traffic speed, weather, and calculates congestion level for a node."""
    node_id, node_info = resolve_node_info(location_query)
    lat, lon = node_info["lat"], node_info["lon"]
    
    flow_data, traffic_is_live, traffic_msg = fetch_tomtom_traffic(lat, lon, api_key)
    weather_data, weather_is_live, weather_msg = fetch_open_meteo_weather(lat, lon)
    
    sample_flow, sample_weather = load_sample_fallback(node_id)
>>>>>>> e809fb07cd44c9b807ba2731379e2fc01fec6502
    if not traffic_is_live:
        flow_data = sample_flow
    if not weather_is_live:
        weather_data = sample_weather
        
    current_speed = float(flow_data.get("currentSpeed", node_info["speed_limit"] * 0.5))
    free_flow_speed = float(flow_data.get("freeFlowSpeed", node_info["speed_limit"]))
    if free_flow_speed <= 0:
        free_flow_speed = float(node_info["speed_limit"])
        
    speed_ratio = current_speed / free_flow_speed
    live_level = speed_ratio_to_level(speed_ratio)
    live_index = level_to_midpoint_index(live_level)
    
    return {
        "node_id": node_id,
        "name": node_info["name"],
        "zone": node_info["zone"],
        "road_type": node_info["road_type"],
        "segment_km": node_info["segment_km"],
        "speed_limit": node_info["speed_limit"],
        "lat": lat,
        "lon": lon,
        "current_speed": round(current_speed, 1),
        "free_flow_speed": round(free_flow_speed, 1),
        "speed_ratio": round(speed_ratio, 4),
        "live_level": live_level,
        "live_index": live_index,
        "traffic_is_live": traffic_is_live,
        "traffic_status": traffic_msg,
        "weather": weather_data,
        "weather_is_live": weather_is_live,
        "weather_status": weather_msg
    }


def get_live_point_data(point_id: str, simulated_ratio: float = None) -> Dict[str, Any]:
    """Bridge for Feature 3 & 4 point lookups."""
    res = get_live_data_and_level(point_id)
    if simulated_ratio is not None:
        res["speed_ratio"] = simulated_ratio
        res["live_level"] = speed_ratio_to_level(simulated_ratio)
        res["live_index"] = level_to_midpoint_index(res["live_level"])
        res["is_simulated"] = True
    else:
        res["is_simulated"] = False
    res["point_id"] = point_id
    res["ratio"] = res["speed_ratio"]
    res["api_ok"] = res["traffic_is_live"]
    return res
