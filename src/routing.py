"""
Route calculation and along-route traffic prediction module.
Features:
1. Geocodes Indian locations (cities, landmarks, addresses).
2. Calculates driving routes between any Source and Destination across India via TomTom Routing API.
3. Samples key checkpoints along the route polyline.
4. Partitions the polyline into sub-segments and predicts traffic congestion for each segment using the model.
5. Returns colored sub-polylines and heatmap points for Google Maps-style rendering.
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import numpy as np

load_dotenv()
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")

from src.utils import ratio_to_level_and_index, index_to_level, get_level_color
from src.profile import predict_profile


def geocode_location(query: str) -> dict:
    """
    Geocodes an Indian place/address name to latitude and longitude.
    Returns dict: {'lat': float, 'lon': float, 'name': str, 'found': bool}
    """
    if not TOMTOM_API_KEY:
        return {"found": False, "error": "TOMTOM_API_KEY missing in .env"}

    query_clean = query.strip()
    if not query_clean:
        return {"found": False, "error": "Query is empty"}

    url = (
        f"https://api.tomtom.com/search/2/geocode/{requests.utils.quote(query_clean)}.json"
        f"?key={TOMTOM_API_KEY}&countrySet=IN&limit=1"
    )
    try:
        resp = requests.get(url, timeout=7)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                pos = results[0].get("position", {})
                address = results[0].get("address", {})
                freeform = address.get("freeformAddress", query_clean)
                return {
                    "lat": float(pos.get("lat")),
                    "lon": float(pos.get("lon")),
                    "name": freeform,
                    "found": True
                }
    except Exception as e:
        return {"found": False, "error": str(e)}

    return {"found": False, "error": f"Location '{query_clean}' not found in India"}


def fetch_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> dict:
    """
    Calculates driving route between source and destination using TomTom Routing API.
    """
    if not TOMTOM_API_KEY:
        return {"success": False, "error": "TOMTOM_API_KEY missing"}

    url = (
        f"https://api.tomtom.com/routing/1/calculateRoute/"
        f"{start_lat},{start_lon}:{end_lat},{end_lon}/json"
        f"?key={TOMTOM_API_KEY}&traffic=true&computeTravelTimeFor=all"
    )
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            routes = data.get("routes", [])
            if routes:
                route = routes[0]
                summary = route.get("summary", {})
                legs = route.get("legs", [])
                polyline = []
                for leg in legs:
                    for pt in leg.get("points", []):
                        polyline.append([float(pt["latitude"]), float(pt["longitude"])])

                return {
                    "success": True,
                    "polyline": polyline,
                    "length_km": round(summary.get("lengthInMeters", 0) / 1000.0, 2),
                    "travel_time_min": round(summary.get("travelTimeInSeconds", 0) / 60.0, 1),
                    "traffic_delay_min": round(summary.get("trafficDelayInSeconds", 0) / 60.0, 1),
                    "departure_time": summary.get("departureTime", ""),
                    "arrival_time": summary.get("arrivalTime", "")
                }
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {"success": False, "error": "Unable to compute route"}


def predict_route_traffic(polyline: list, horizon_minutes: int = 30) -> list:
    """
    Partitions the entire route polyline into contiguous segments (sub-polylines),
    fetches live flow for each segment's midpoint, and applies the ML blended model.
    Each segment gets:
    - coordinates (sub_polyline)
    - predicted congestion level & color (Google Maps style: Green, Orange, Red)
    - congestion index for heatmaps
    """
    if not polyline:
        return []

    total_pts = len(polyline)
    num_segments = min(12, max(4, total_pts // 15))
    pts_per_seg = max(2, total_pts // num_segments)

    now_dt = datetime.now()
    target_dt = now_dt + timedelta(minutes=horizon_minutes)
    model_profile_index = predict_profile(target_dt)

    segments = []

    for i in range(num_segments):
        start_idx = i * pts_per_seg
        end_idx = (i + 1) * pts_per_seg if i < num_segments - 1 else total_pts
        sub_pts = polyline[start_idx:end_idx + 1]

        if not sub_pts:
            continue

        # Sample midpoint of this sub-segment
        mid_pt = sub_pts[len(sub_pts) // 2]
        lat, lon = mid_pt[0], mid_pt[1]

        cur_speed = 40.0
        ff_speed = 50.0
        ratio = 0.85
        api_ok = False

        if TOMTOM_API_KEY:
            flow_url = (
                f"https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"
                f"?point={lat},{lon}&key={TOMTOM_API_KEY}&unit=KMPH"
            )
            try:
                r = requests.get(flow_url, timeout=4)
                if r.status_code == 200:
                    flow = r.json().get("flowSegmentData", {})
                    cur_speed = float(flow.get("currentSpeed", 40.0))
                    ff_speed = float(flow.get("freeFlowSpeed", 50.0))
                    if ff_speed > 0:
                        ratio = round(cur_speed / ff_speed, 3)
                        api_ok = True
            except Exception:
                pass

        cur_level, cur_index = ratio_to_level_and_index(ratio)

        # Blended Prediction: 0.55 live + 0.45 model profile
        pred_index = float(np.clip(0.55 * cur_index + 0.45 * model_profile_index, 0.0, 1.0))
        pred_level = index_to_level(pred_index)

        progress_pct = int((i / max(1, num_segments - 1)) * 100)

        # Google Maps traffic coloring:
        # Low -> Green (#00e676), Moderate -> Yellow (#ffea00), High -> Orange (#ff9100), Severe -> Red (#d50000)
        color_map = {
            "Low": "#00c853",        # Green (Free flow)
            "Moderate": "#ffd600",   # Yellow (Slowing)
            "High": "#ff6d00",       # Orange (Heavy)
            "Severe": "#d50000"      # Dark Red (Standstill)
        }

        segments.append({
            "segment_idx": i + 1,
            "progress_pct": progress_pct,
            "lat": lat,
            "lon": lon,
            "sub_polyline": sub_pts,
            "current_speed": cur_speed,
            "free_flow_speed": ff_speed,
            "current_ratio": ratio,
            "current_level": cur_level,
            "predicted_index": round(pred_index, 3),
            "predicted_level": pred_level,
            "color": color_map.get(pred_level, "#00c853"),
            "api_ok": api_ok
        })

    return segments
