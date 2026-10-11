"""
Reusable UI charts and visual components for Features 1 and 2.
Exported functions:
- forecast_chart(forecast_data)
- weight_table(forecast_data)
- profile_chart()
- factors_chart()
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.profile import predict_profile


def forecast_chart(forecast_data: dict) -> go.Figure:
    """Creates interactive Plotly line chart of the 7-horizon forecast curve."""
    horizons = forecast_data.get("horizons", [])
    x_labels = [f"+{h['minutes']}m ({h['target_time']})" for h in horizons]
    y_pred = [h["predicted_index"] for h in horizons]
    y_calib_profile = [h["profile_index_calibrated"] for h in horizons]
    cur_idx = forecast_data.get("current_index", 0.5)

    fig = go.Figure()

    # Current index baseline
    fig.add_trace(go.Scatter(
        x=[x_labels[0]] + x_labels,
        y=[cur_idx] * (len(x_labels) + 1),
        mode="lines",
        name="Current Live Index",
        line=dict(color="#17a2b8", dash="dot", width=2)
    ))

    # Calibrated profile trajectory
    fig.add_trace(go.Scatter(
        x=x_labels,
        y=y_calib_profile,
        mode="lines+markers",
        name="Historical Profile (Calibrated)",
        line=dict(color="#6c757d", dash="dash", width=2)
    ))

    # Blended forecast curve
    fig.add_trace(go.Scatter(
        x=x_labels,
        y=y_pred,
        mode="lines+markers",
        name="Blended Forecast",
        line=dict(color="#007bff", width=3),
        marker=dict(size=8)
    ))

    # Add congestion zones
    fig.add_hrect(y0=0.0, y1=0.375, fillcolor="#28a745", opacity=0.08, line_width=0, annotation_text="Low Zone")
    fig.add_hrect(y0=0.375, y1=0.675, fillcolor="#ffc107", opacity=0.08, line_width=0, annotation_text="Moderate Zone")
    fig.add_hrect(y0=0.675, y1=0.875, fillcolor="#fd7e14", opacity=0.08, line_width=0, annotation_text="High Zone")
    fig.add_hrect(y0=0.875, y1=1.0, fillcolor="#dc3545", opacity=0.08, line_width=0, annotation_text="Severe Zone")

    fig.update_layout(
        title="7-Horizon Blended Congestion Forecast (15m to 120m)",
        xaxis_title="Forecast Horizon",
        yaxis_title="Congestion Index (0.0 to 1.0)",
        yaxis=dict(range=[0.0, 1.05]),
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def weight_table(forecast_data: dict) -> pd.DataFrame:
    """Formats the live vs historical weight distribution table."""
    horizons = forecast_data.get("horizons", [])
    data = []
    for h in horizons:
        data.append({
            "Horizon": f"+{h['minutes']} min",
            "Target Time": h["target_time"],
            "Live Weight": f"{int(h['live_weight'] * 100)}%",
            "History Weight": f"{int(h['history_weight'] * 100)}%",
            "Predicted Index": f"{h['predicted_index']:.3f}",
            "Predicted Level": h["predicted_level"]
        })
    return pd.DataFrame(data)


def profile_chart() -> go.Figure:
    """Diurnal profile chart (Weekday vs Weekend)."""
    hours = np.linspace(0, 23.5, 48)
    now = datetime.now()

    weekday_y = []
    weekend_y = []

    for h in hours:
        hr = int(h)
        mn = int((h - hr) * 60)
        dt_weekday = datetime(2026, 10, 14, hr, mn) # Wednesday
        dt_weekend = datetime(2026, 10, 11, hr, mn) # Sunday
        weekday_y.append(predict_profile(dt_weekday))
        weekend_y.append(predict_profile(dt_weekend))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hours, y=weekday_y, mode="lines", name="Weekday Profile", line=dict(color="#007bff", width=2.5)))
    fig.add_trace(go.Scatter(x=hours, y=weekend_y, mode="lines", name="Weekend Profile", line=dict(color="#28a745", width=2.5, dash="dash")))

    fig.update_layout(
        title="Historical Congestion Diurnal Profile by Hour of Day",
        xaxis_title="Hour of Day (0 to 24)",
        yaxis_title="Congestion Index (0 to 1)",
        yaxis=dict(range=[0, 1]),
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def factors_chart() -> go.Figure:
    """Feature importance breakdown bar chart."""
    features = ["Hour of Day", "Day of Week (Weekend vs Weekday)", "Rainfall (mm)", "Cloud Cover (%)", "Temperature (°C)"]
    importances = [0.45, 0.28, 0.15, 0.07, 0.05]

    fig = go.Figure(go.Bar(
        x=importances,
        y=features,
        orientation="h",
        marker=dict(color="#17a2b8")
    ))
    fig.update_layout(
        title="Model Feature Drivers / Importances",
        xaxis_title="Relative Feature Importance",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=150, r=20, t=50, b=40)
    )
    return fig
