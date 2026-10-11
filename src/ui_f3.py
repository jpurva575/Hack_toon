import datetime
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any

from src.config import NODES_CONFIG, LEVEL_COLORS, DEFAULT_TAU
from src.live import get_live_data_and_level
from src.blend import forecast_horizons
from src.delay import estimate_segment_delay


def render_feature3_tab(meta: Dict[str, Any]):
    st.header("⏱️ Feature 3: Traffic Impact & Delay Estimator")
    st.caption("Quantifies extra commuter travel time by comparing free-flow baseline with current and predicted horizon travel times.")

    col_node, col_spd = st.columns([2, 2])
    with col_node:
        selected_node_id = st.selectbox(
            "Select Road Segment for Delay Analysis",
            options=list(NODES_CONFIG.keys()),
            format_func=lambda x: f"{NODES_CONFIG[x]['name']} ({NODES_CONFIG[x]['segment_km']} km)",
            key="f3_node_select"
        )
        node_info = NODES_CONFIG[selected_node_id]
        
    # Get live speed as baseline
    live_res = get_live_data_and_level(selected_node_id)
    with col_spd:
        curr_spd_input = st.slider(
            "Current Observed Speed (km/h)",
            min_value=5.0,
            max_value=float(node_info["speed_limit"]),
            value=float(live_res["current_speed"]),
            step=1.0,
            key="f3_speed_slider"
        )

    # 7-Horizon predictions for this node
    now = datetime.datetime.now()
    curr_ratio = curr_spd_input / node_info["speed_limit"]
    from src.live import speed_ratio_to_level, level_to_midpoint_index
    lvl = speed_ratio_to_level(curr_ratio)
    idx = level_to_midpoint_index(lvl)
    forecasts = forecast_horizons(now, live_index=idx, meta=meta, tau=DEFAULT_TAU)

    # Compute delay metrics
    impact = estimate_segment_delay(selected_node_id, curr_spd_input, forecasts)

    # Display KPI Cards
    st.markdown("### 📊 Segment Impact Metrics")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Free-Flow Time", f"{impact['free_flow_time_min']:.1f} min", help=f"At speed limit of {impact['speed_limit']} km/h")
    with c2:
        st.metric("Current Travel Time", f"{impact['current_time_min']:.1f} min")
    with c3:
        st.metric("Added Delay", f"+{impact['current_delay_min']:.1f} min", delta=f"{impact['current_delay_min']:.1f} min", delta_color="inverse")
    with c4:
        st.metric("Travel Time Index (TTI)", f"{impact['current_tti']:.2f}", help="TTI = Actual Time / Free-flow Time")
    with c5:
        st.metric("Speed Reduction", f"-{impact['speed_drop_pct']:.0f}%", delta=f"-{impact['speed_drop_pct']:.0f}%", delta_color="inverse")

    # Commuter advice callout
    st.info(f"💡 **Commuter Recommendation:** {impact['advice']}")

    st.markdown("---")

    # Horizon Delay Breakdown
    col_chart, col_tbl = st.columns([3, 2])
    with col_chart:
        st.subheader("📈 Projected Departure Delay Across Horizons")
        horizons_data = impact["horizon_delays"]
        h_labels = [f"+{h['horizon_min']}m" for h in horizons_data]
        free_vals = [impact["free_flow_time_min"] for _ in horizons_data]
        delay_vals = [h["delay_min"] for h in horizons_data]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=h_labels,
            y=free_vals,
            name="Free-Flow Travel Time (min)",
            marker_color="#28a745"
        ))
        fig.add_trace(go.Bar(
            x=h_labels,
            y=delay_vals,
            name="Congestion Delay (min)",
            marker_color="#dc3545"
        ))
        fig.update_layout(
            barmode="stack",
            height=340,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Departure Horizon",
            yaxis_title="Total Minutes Required",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_tbl:
        st.subheader("📋 Horizon Delay Schedule")
        df_delays = pd.DataFrame({
            "Departure": [f"+{h['horizon_min']} min" for h in horizons_data],
            "Est Speed": [f"{h['speed_kmh']:.0f} km/h" for h in horizons_data],
            "Trip Time": [f"{h['travel_time_min']:.1f} min" for h in horizons_data],
            "Added Delay": [f"+{h['delay_min']:.1f} min" for h in horizons_data],
            "TTI": [f"{h['tti']:.2f}" for h in horizons_data]
        })
        st.dataframe(df_delays, use_container_width=True, hide_index=True)
