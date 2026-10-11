import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any

from src.config import ROUTES_CONFIG, LEVEL_COLORS
from src.routes import compare_route_pair
from src.alerts import evaluate_congestion_alerts
from src.live import get_live_data_and_level
from src.blend import forecast_horizons


def render_feature5_tab(meta: Dict[str, Any]):
    st.header("🛣️ Feature 5: Route Comparison & Proactive Alert System")
    st.caption("Compares alternative arterial routes across current and future departure times, and triggers advance warnings for severe congestion.")

    # Section 1: Route Comparison System
    st.subheader("1. Alternative Route Comparison")
    
    col_pair, col_dep = st.columns([3, 2])
    with col_pair:
        pair_key = st.selectbox(
            "Select Origin–Destination Corridor Pair",
            options=list(ROUTES_CONFIG.keys()),
            format_func=lambda k: f"{ROUTES_CONFIG[k]['name']} ({ROUTES_CONFIG[k]['origin']} ➔ {ROUTES_CONFIG[k]['destination']})"
        )
    with col_dep:
        departure_horizon = st.selectbox(
            "Departure Horizon Window",
            options=[0, 15, 30, 60],
            format_func=lambda h: "Depart Now (Live Traffic)" if h == 0 else f"Depart in +{h} Minutes"
        )

    res = compare_route_pair(pair_key, meta=meta, departure_horizon=departure_horizon)

    # Recommendation Callout Card
    st.markdown(
        f"""
        <div style="background-color: {res['badge_color']}18; border-left: 6px solid {res['badge_color']}; padding: 16px; border-radius: 8px; margin: 12px 0;">
            <h3 style="margin: 0; color: {res['badge_color']};">Recommended Route: {res['recommended_route']}</h3>
            <p style="margin: 6px 0 0 0; font-size: 1rem; color: #333;">{res['recommendation_reason']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Side-by-Side Route Metrics
    c_ra, c_rb = st.columns(2)
    with c_ra:
        st.markdown(f"#### 🅰️ {res['route_a_name']}")
        ma = res["metrics_a"]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Distance", f"{ma['total_distance_km']} km")
            st.metric("Trip Travel Time", f"{res['effective_time_a']:.1f} min")
        with c2:
            st.metric("Free-Flow Time", f"{ma['free_flow_time_min']:.1f} min")
            st.metric("Congestion Delay", f"+{ma['current_delay_min']:.1f} min", delta_color="inverse")
        with c3:
            st.metric("Avg Speed", f"{ma['average_speed_kmh']} km/h")
            st.caption(f"Worst Choke: **{ma['worst_bottleneck_node']}** (-{ma['worst_slowdown_pct']}%)")

    with c_rb:
        st.markdown(f"#### 🅱️ {res['route_b_name']}")
        mb = res["metrics_b"]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Distance", f"{mb['total_distance_km']} km")
            st.metric("Trip Travel Time", f"{res['effective_time_b']:.1f} min")
        with c2:
            st.metric("Free-Flow Time", f"{mb['free_flow_time_min']:.1f} min")
            st.metric("Congestion Delay", f"+{mb['current_delay_min']:.1f} min", delta_color="inverse")
        with c3:
            st.metric("Avg Speed", f"{mb['average_speed_kmh']} km/h")
            st.caption(f"Worst Choke: **{mb['worst_bottleneck_node']}** (-{mb['worst_slowdown_pct']}%)")

    # Comparative Travel Time Chart Across Departure Horizons
    st.markdown("##### ⏱️ Comparative Travel Times Across Future Departure Windows")
    horizons = ["Now", "+15m", "+30m", "+60m"]
    times_a = [ma["current_time_min"], ma["time_at_15m"], ma["time_at_30m"], ma["time_at_60m"]]
    times_b = [mb["current_time_min"], mb["time_at_15m"], mb["time_at_30m"], mb["time_at_60m"]]

    fig_cmp = go.Figure()
    fig_cmp.add_trace(go.Bar(x=horizons, y=times_a, name=res["route_a_name"], marker_color="#0066cc"))
    fig_cmp.add_trace(go.Bar(x=horizons, y=times_b, name=res["route_b_name"], marker_color="#ff7f0e"))
    fig_cmp.update_layout(
        barmode="group",
        height=280,
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis_title="Estimated Travel Time (Minutes)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_cmp, use_container_width=True)

    st.markdown("---")

    # Section 2: Proactive Congestion Alert System
    st.subheader("2. Proactive Network Congestion Alerts")
    st.caption("Active surveillance engine flagging imminent severe congestion surges across critical junctions.")

    col_alert_cfg1, col_alert_cfg2 = st.columns(2)
    with col_alert_cfg1:
        alert_node = st.selectbox(
            "Monitored Alert Corridor",
            options=["MUM_EEH_01", "MUM_DADAR_03", "THN_NODE_01", "MUM_TOLL_01", "MUM_WEH_02"],
            format_func=lambda nid: f"{ROUTES_CONFIG['ROUTE_PAIR_1']['route_a']['name']} - {nid}",
            key="f5_alert_node"
        )
    with col_alert_cfg2:
        delay_thresh = st.slider("Alert Trigger Delay Threshold (Minutes)", min_value=5.0, max_value=30.0, value=12.0, step=1.0)

    # Evaluate alerts
    from src.live import level_to_midpoint_index
    from src.config import NODES_CONFIG
    node_name = NODES_CONFIG[alert_node]["name"]
    live_info = get_live_data_and_level(alert_node)
    fcasts = forecast_horizons(
        now=None,
        live_index=level_to_midpoint_index(live_info["live_level"]),
        meta=meta
    )
    alert_res = evaluate_congestion_alerts(node_name, fcasts, delay_threshold_min=delay_thresh)

    st.markdown(
        f"""
        <div style="background-color: {alert_res['badge_color']}18; border-left: 6px solid {alert_res['badge_color']}; padding: 14px; border-radius: 6px; margin-top: 10px;">
            <b style="color: {alert_res['badge_color']}; font-size: 1.1rem;">{alert_res['title']}</b>
            <p style="margin: 4px 0 0 0; color: #333; font-size: 0.95rem;">{alert_res['message']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
