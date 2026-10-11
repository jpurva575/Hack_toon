import os
import json
import logging
from typing import Dict, Any, Tuple
import requests
from dotenv import load_dotenv

from src.config import (
    LOCATIONS,
    SPEED_RATIO_THRESHOLDS,
    LEVEL_MIDPOINTS,
    SAMPLE_LIVE_PATH
)

load_dotenv()
logging.basicConfig(level=logging.INFO)


def load_sample_fallback(location_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Loads saved sample live response from data/sample_live.json when offline or API key absent.
    """
    if SAMPLE_LIVE_PATH.exists():
        with open(SAMPLE_LIVE_PATH, "r") as f:
            data = json.load(f)
        if location_name in data:
            loc_data = data[location_name]
            return loc_data.get("flowSegmentData", {}), loc_data.get("weather", {})
            
    # Generic hardcoded fallback if sample file is missing
    fallback_flow = {
        "currentSpeed": 35,
        "freeFlowSpeed": 60,
        "currentTravelTime": 170,
        "freeFlowTravelTime": 100,
        "confidence": 0.90
    }
    fallback_weather = {
        "temperature_2m": 30.0,
        "precipitation": 0.0,
        "cloud_cover": 20
    }
    return fallback_flow, fallback_weather


def fetch_tomtom_traffic(lat: float, lon: float, api_key: str = None) -> Tuple[Dict[str, Any], bool, str]:
    """
    Calls TomTom Traffic Flow Segment API.
    Returns: (flowSegmentData, is_live, status_message)
    """
    key = api_key or os.getenv("TOMTOM_API_KEY")
    if not key or key.strip() == "":
        return {}, False, "No TomTom API key provided. Using verified sample fallback."
        
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
    params = {
        "point": f"{lat},{lon}",
        "key": key
    }
    
    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            flow_data = data.get("flowSegmentData", {})
            if "currentSpeed" in flow_data and "freeFlowSpeed" in flow_data:
                return flow_data, True, "Live TomTom Flow Segment API response"
            else:
                return {}, False, f"TomTom API response missing speed data: {resp.text[:100]}"
        else:
            return {}, False, f"TomTom API HTTP {resp.status_code}: {resp.text[:100]}"
    except Exception as e:
        return {}, False, f"TomTom API connection error: {str(e)}"


def fetch_open_meteo_weather(lat: float, lon: float) -> Tuple[Dict[str, Any], bool, str]:
    """
    Calls Open-Meteo free weather API.
    Returns: (weather_dict, is_live, status_message)
    """
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
                "temperature_2m": current.get("temperature_2m", 28.0),
                "precipitation": current.get("precipitation", 0.0),
                "cloud_cover": current.get("cloud_cover", 30)
            }, True, "Live Open-Meteo API response"
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
    """
    Converts congestion level to common index in [0, 1] using midpoints of percentile bands:
    Low: 0.20, Moderate: 0.55, High: 0.80, Severe: 0.95
    """
    return LEVEL_MIDPOINTS.get(level, 0.55)


def get_live_data_and_level(
    location_name: str,
    api_key: str = None
) -> Dict[str, Any]:
    """
    Orchestrates live traffic and weather retrieval with fallback.
    Computes speed ratio, live congestion level, and live midpoint index.
    """
    loc = LOCATIONS.get(location_name, LOCATIONS["Mumbai"])
    lat, lon = loc["lat"], loc["lon"]
    
    # 1. Fetch traffic
    flow_data, traffic_is_live, traffic_msg = fetch_tomtom_traffic(lat, lon, api_key)
    
    # 2. Fetch weather
    weather_data, weather_is_live, weather_msg = fetch_open_meteo_weather(lat, lon)
    
    # Fallback check
    sample_flow, sample_weather = load_sample_fallback(location_name)
    
    if not traffic_is_live:
        flow_data = sample_flow
    if not weather_is_live:
        weather_data = sample_weather
        
    current_speed = float(flow_data.get("currentSpeed", 30))
    free_flow_speed = float(flow_data.get("freeFlowSpeed", 60))
    if free_flow_speed <= 0:
        free_flow_speed = 60.0
        
    speed_ratio = current_speed / free_flow_speed
    live_level = speed_ratio_to_level(speed_ratio)
    live_index = level_to_midpoint_index(live_level)
    
    return {
        "location": location_name,
        "lat": lat,
        "lon": lon,
        "current_speed": current_speed,
        "free_flow_speed": free_flow_speed,
        "speed_ratio": round(speed_ratio, 4),
        "live_level": live_level,
        "live_index": live_index,
        "traffic_is_live": traffic_is_live,
        "traffic_status": traffic_msg,
        "weather": weather_data,
        "weather_is_live": weather_is_live,
        "weather_status": weather_msg
    }
