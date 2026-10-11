"""
Shared utilities for traffic ratio, level, and index conversions.
Used identically across Features 2, 3, and 4.
"""

from typing import Tuple

def ratio_to_level_and_index(ratio: float) -> Tuple[str, float]:
    """
    Converts a live traffic speed ratio (current_speed / free_flow_speed)
    to a standardized traffic congestion level and congestion index.
    Thresholds:
      ratio > 0.8  -> Low (0.20)
      0.6 < ratio <= 0.8 -> Moderate (0.55)
      0.4 < ratio <= 0.6 -> High (0.80)
      ratio <= 0.4 -> Severe (0.95)
    """
    if ratio > 0.8:
        return "Low", 0.20
    elif ratio > 0.6:
        return "Moderate", 0.55
    elif ratio > 0.4:
        return "High", 0.80
    else:
        return "Severe", 0.95


def index_to_level(index: float) -> str:
    """
    Converts a continuous congestion index in [0, 1] to the closest discrete level.
    Midpoints: Low=0.20, Moderate=0.55, High=0.80, Severe=0.95
    Boundary cutoffs:
      index < 0.375  -> Low
      0.375 <= index < 0.675 -> Moderate
      0.675 <= index < 0.875 -> High
      index >= 0.875 -> Severe
    """
    if index < 0.375:
        return "Low"
    elif index < 0.675:
        return "Moderate"
    elif index < 0.875:
        return "High"
    else:
        return "Severe"


def get_level_color(level: str) -> str:
    """Returns the hex color code for a given traffic level."""
    colors = {
        "Low": "#28a745",       # Green
        "Moderate": "#ffc107",  # Yellow
        "High": "#fd7e14",      # Orange
        "Severe": "#dc3545"     # Red
    }
    return colors.get(level, "#6c757d")
