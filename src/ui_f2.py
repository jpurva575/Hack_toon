import datetime
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any

from src.config import (
    LOCATIONS,
    LEVEL_COLORS,
    LEVEL_NAMES,
    DEFAULT_TAU
)
from src.live import (
    get_live_data_and_level,
    speed_ratio_to_level,
    level_to_midpoint_index
)
from src.blend import forecast_horizons


def render_feature2_tab(meta: Dict[str, Any]):
    st.header("⚡ Feature 2: Live Integration & 5–120 min Forecasting")
    st.caption("Blends instantaneous live road speed deviations with historical profiles across 7 forecasting horizons.")

    # Location selection and API trigger
    col_loc, col_action = st.columns([3, 1])
    with col_loc:
        selected_location = st.selectbox(
            "Select Road Corridor / City",
            options=list(LOCATIONS.keys()),
            help="Predefined geographic coordinates for key Maharashtra corridors"
        )
        loc_info = LOCATIONS[selected_location]
        st.caption(f"📍 Coordinates: Lat {loc_info['lat']}, Lon {loc_info['lon']} — *{loc_info['description']}*")
        
    with col_action:
        st.write("")
        st.write("")
        fetch_btn = st.button("🔄 Fetch Live Status", type="primary", use_container_width=True)

    # Session state for live data cache
    cache_key = f"live_data_{selected_location}"
    if fetch_btn or cache_key not in st.session_state:
        with st.spinner("Calling Traffic & Weather APIs..."):
            st.session_state[cache_key] = get_live_data_and_level(selected_location)

    live_res = st.session_state[cache_key]

    # Live Status Summary Card
    st.markdown("### 📡 Live Conditions Snapshot")
    col_spd, col_ratio, col_lvl, col_wth = st.columns(4)

    with col_spd:
        st.metric(
            "Current / Free-Flow Speed",
            f"{live_res['current_speed']:.0f} / {live_res['free_flow_speed']:.0f} km/h"
        )
    with col_ratio:
        st.metric(
            "Observed Speed Ratio",
            f"{live_res['speed_ratio']:.2f}",
            help="Ratio = currentSpeed / freeFlowSpeed. Values below 0.6 indicate congestion."
        )
    with col_lvl:
        live_level_name = live_res["live_level"]
        badge_col = LEVEL_COLORS.get(live_level_name, "#6c757d")
        st.markdown(
            f"""
            <div style="background-color: {badge_col}22; border: 1px solid {badge_col}; border-radius: 6px; padding: 10px; text-align: center;">
                <span style="color: {badge_col}; font-weight: bold; font-size: 1.15rem;">Live: {live_level_name}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_wth:
        wth = live_res["weather"]
        st.metric(
            "Local Weather",
            f"{wth.get('temperature_2m', 30):.1f}°C",
            delta=f"Rain: {wth.get('precipitation', 0.0):.1f}mm | Cloud: {wth.get('cloud_cover', 20)}%"
        )

    # API connection status banner
    if live_res["traffic_is_live"]:
        st.success(f"Connected: {live_res['traffic_status']}")
    else:
        st.info(f"ℹ️ Fallback Mode Active: {live_res['traffic_status']}")

    st.markdown("---")

    # Interactive Simulator Slider
    st.subheader("🧪 Live Speed Ratio Simulator")
    st.caption("Test how instant speed fluctuations propagate into short vs long horizon forecasts.")
    
    sim_ratio = st.slider(
        "Simulate live speed ratio (Overrides live value for interactive testing)",
        min_value=0.10,
        max_value=1.00,
        value=float(live_res["speed_ratio"]),
        step=0.05,
        help="Simulate severe traffic by dragging to 0.30, or smooth flow by dragging to 0.90."
    )
    
    # Effective live calculation based on simulated/active ratio
    effective_level = speed_ratio_to_level(sim_ratio)
    effective_index = level_to_midpoint_index(effective_level)

    if round(sim_ratio, 2) != round(live_res["speed_ratio"], 2):
        st.warning(f"Simulated Ratio: **{sim_ratio:.2f}** $\\rightarrow$ Level: **{effective_level}** (Midpoint index: {effective_index:.2f})")

    # Forecast calculation across 7 horizons
    now = datetime.datetime.now()
    forecasts = forecast_horizons(
        now=now,
        live_index=effective_index,
        meta=meta,
        tau=DEFAULT_TAU
    )

    # Forecast Cards Row (7 Horizons)
    st.markdown("### ⏱️ 7-Horizon Congestion Forecast (5–120 min)")
    f_cols = st.columns(7)
    for idx, f in enumerate(forecasts):
        with f_cols[idx]:
            f_color = LEVEL_COLORS.get(f["predicted_level"], "#6c757d")
            st.markdown(
                f"""
                <div style="background-color: {f_color}18; border-top: 4px solid {f_color}; border-radius: 6px; padding: 8px 4px; text-align: center; margin-bottom: 8px;">
                    <div style="font-size: 0.85rem; color: #666; font-weight: 600;">+{f['horizon_min']} min</div>
                    <div style="font-size: 0.75rem; color: #888;">{f['future_time']}</div>
                    <div style="font-size: 1.05rem; font-weight: bold; color: {f_color}; margin: 4px 0;">{f['predicted_level']}</div>
                    <div style="font-size: 0.75rem; color: #555;">Index: <b>{f['blended_index']:.2f}</b></div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Forecast Chart and Weights Table
    c_left, c_right = st.columns([3, 2])

    with c_left:
        st.subheader("📊 Forecast Progression Chart")
        
        horizon_labels = [f"+{f['horizon_min']}m\n({f['future_time']})" for f in forecasts]
        blended_vals = [f["blended_index"] for f in forecasts]
        profile_vals = [f["profile_index"] for f in forecasts]
        
        fig = go.Figure()
        
        # Color bands for congestion zones
        fig.add_hrect(y0=0.0, y1=0.40, fillcolor="rgba(40, 167, 69, 0.12)", line_width=0, annotation_text="Low", annotation_position="top left")
        fig.add_hrect(y0=0.40, y1=0.70, fillcolor="rgba(255, 193, 7, 0.12)", line_width=0, annotation_text="Moderate", annotation_position="top left")
        fig.add_hrect(y0=0.70, y1=0.90, fillcolor="rgba(253, 126, 20, 0.12)", line_width=0, annotation_text="High", annotation_position="top left")
        fig.add_hrect(y0=0.90, y1=1.00, fillcolor="rgba(220, 53, 69, 0.12)", line_width=0, annotation_text="Severe", annotation_position="top left")
        
        # Historical profile line
        fig.add_trace(go.Scatter(
            x=horizon_labels,
            y=profile_vals,
            mode="lines+markers",
            name="Historical Profile",
            line=dict(color="#6c757d", dash="dash", width=2)
        ))
        
        # Blended forecast line
        fig.add_trace(go.Scatter(
            x=horizon_labels,
            y=blended_vals,
            mode="lines+markers",
            name="Blended Forecast",
            line=dict(color="#0066cc", width=4),
            marker=dict(size=10, color=[LEVEL_COLORS[f["predicted_level"]] for f in forecasts])
        ))
        
        fig.update_layout(
            height=360,
            margin=dict(l=20, r=20, t=20, b=20),
            yaxis=dict(title="Congestion Index [0–1]", range=[0.0, 1.05]),
            xaxis=dict(title="Forecasting Horizon"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with c_right:
        st.subheader("⚖️ Live vs. History Weight Distribution")
        
        table_df = pd.DataFrame({
            "Horizon": [f"{f['horizon_min']} min" for f in forecasts],
            "Live Wt": [f"{f['weight_live_pct']:.0f}%" for f in forecasts],
            "Hist Wt": [f"{f['weight_history_pct']:.0f}%" for f in forecasts],
            "Blended Index": [f"{f['blended_index']:.2f}" for f in forecasts],
            "Level": [f["predicted_level"] for f in forecasts]
        })
        st.dataframe(table_df, use_container_width=True, hide_index=True)
        
        st.markdown(
            f"""
            <div style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 12px; font-size: 0.85rem; color: #495057;">
                <b>Mathematical Blend Formula:</b><br/>
                <code>index(h) = profile(now + h) + (live_index − profile(now)) × exp(−h / {DEFAULT_TAU:.0f})</code><br/><br/>
                Notice that at <b>5 min</b>, live observation accounts for <b>92%</b> of the prediction. By <b>120 min</b>, it decays to <b>14%</b>, allowing historical recurring trends to govern.
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.caption("⚠️ **Limits & Engineering Disclaimers:** Historical dataset is hourly; sub-hour points are linearly interpolated. Cross-regional transfer to Mumbai/Pune/Konkan is an assumed reference pattern and not validated on local Indian sensor streams.")
