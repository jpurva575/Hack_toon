<<<<<<< HEAD
"""
Pan-India Route & Google Maps-Style Traffic Heatmap Dashboard (Feature 4).
Capabilities:
1. Origin and Destination inputs anywhere in India.
2. Route computation via TomTom Routing API.
3. Google Maps Traffic Overlay:
   - Colored Road Heatmap / Segmented Polylines (🟢 Free Flow Green, 🟡 Moderate Yellow, 🟠 Heavy Orange, 🔴 Standstill Red).
   - Folium HeatMap layer highlighting congestion intensity zones.
   - Toggle between 'Google Maps Traffic Line' and 'Continuous Heatmap'.
4. ML Along-Route Forecast across horizons (+15m to +120m).
5. Clean journey metrics and checkpoint breakdown.
"""

import os
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from src.routing import geocode_location, fetch_route, predict_route_traffic
from src.utils import get_level_color


@st.cache_data(ttl=180)
def cached_route_and_prediction(start_lat, start_lon, end_lat, end_lon, horizon_min):
    route_data = fetch_route(start_lat, start_lon, end_lat, end_lon)
    if not route_data.get("success"):
        return route_data, []
    traffic_segments = predict_route_traffic(route_data["polyline"], horizon_minutes=horizon_min)
    return route_data, traffic_segments


def render_dashboard():
    st.set_page_config(
        page_title="India Traffic Heatmap & Route Predictor",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🚦 India Road Traffic Heatmap & Route Predictor")
    st.caption("Google Maps-style road traffic overlay and ML model predictions for any journey in India.")

    # ------------------ SIDEBAR: ROUTE PLANNING ------------------
    st.sidebar.header("Route Planner (Pan-India)")
    source_input = st.sidebar.text_input("Source Location", value="Bandra, Mumbai", help="Enter origin in India")
    dest_input = st.sidebar.text_input("Destination Location", value="Koregaon Park, Pune", help="Enter destination in India")

    horizon_min = st.sidebar.selectbox(
        "Forecast Horizon for Route",
        options=[15, 30, 45, 60, 90, 120],
        index=1,
        format_func=lambda m: f"+{m} minutes"
    )

    # Traffic Layer Display Mode
    st.sidebar.markdown("---")
    st.sidebar.subheader("Map Visual Style")
    map_layer_style = st.sidebar.radio(
        "Select Traffic Visualization Style:",
        ["Google Maps Traffic Lines (Colored Roads)", "Congestion Heatmap (Density Gradients)", "Both Overlaid"],
        index=0
    )

    find_route_btn = st.sidebar.button("Calculate Route & Predict Traffic", type="primary")

    # Simulation Controls
    st.sidebar.markdown("---")
    st.sidebar.subheader("Congestion Simulation")
    simulate_toggle = st.sidebar.checkbox("Simulate Traffic Spike along Route", value=False)
    simulated_ratio = None
    if simulate_toggle:
        simulated_ratio = st.sidebar.slider(
            "Simulate Live Speed Ratio",
            min_value=0.10,
            max_value=1.00,
            value=0.35,
            step=0.05,
            help="Simulate heavy congestion (lower = severe)"
        )
        st.sidebar.info(f"Simulating congestion ratio: {simulated_ratio:.2f}")

    # ------------------ PROCESS ROUTE ------------------
    if "route_data" not in st.session_state or find_route_btn:
        with st.spinner("Calculating route and predicting traffic across India..."):
            src_res = geocode_location(source_input)
            dst_res = geocode_location(dest_input)

            if not src_res.get("found"):
                st.error(f"Source not found: {src_res.get('error')}")
                return
            if not dst_res.get("found"):
                st.error(f"Destination not found: {dst_res.get('error')}")
                return

            st.session_state["src_info"] = src_res
            st.session_state["dst_info"] = dst_res

            r_data, segs = cached_route_and_prediction(
                src_res["lat"], src_res["lon"],
                dst_res["lat"], dst_res["lon"],
                horizon_min
            )
            st.session_state["route_data"] = r_data
            st.session_state["route_segments"] = segs

    route_data = st.session_state.get("route_data", {})
    route_segments = st.session_state.get("route_segments", [])
    src_info = st.session_state.get("src_info", {})
    dst_info = st.session_state.get("dst_info", {})

    if not route_data.get("success"):
        st.error(f"Could not calculate route: {route_data.get('error', 'Unknown error')}")
        return

    # Simulation overrides if checked
    if simulate_toggle and simulated_ratio is not None:
        for s in route_segments:
            s["current_ratio"] = simulated_ratio
            if simulated_ratio <= 0.4:
                s["predicted_level"] = "Severe"
                s["predicted_index"] = 0.95
                s["color"] = "#d50000"
            elif simulated_ratio <= 0.6:
                s["predicted_level"] = "High"
                s["predicted_index"] = 0.80
                s["color"] = "#ff6d00"
            elif simulated_ratio <= 0.8:
                s["predicted_level"] = "Moderate"
                s["predicted_index"] = 0.55
                s["color"] = "#ffd600"
            else:
                s["predicted_level"] = "Low"
                s["predicted_index"] = 0.20
                s["color"] = "#00c853"

    # ------------------ TOP SUMMARY METRICS ------------------
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Total Route Distance", f"{route_data['length_km']} km")
    with col_m2:
        st.metric("Estimated Travel Time", f"{route_data['travel_time_min']} mins")
    with col_m3:
        st.metric("Expected Traffic Delay", f"{route_data['traffic_delay_min']} mins")
    with col_m4:
        levels = [s["predicted_level"] for s in route_segments]
        worst_level = "Severe" if "Severe" in levels else ("High" if "High" in levels else ("Moderate" if "Moderate" in levels else "Low"))
        st.metric(f"Peak Predicted Traffic (+{horizon_min}m)", worst_level, delta=f"{len(route_segments)} Segments Evaluated")

    st.markdown(f"**From:** `{src_info.get('name')}`  ➔  **To:** `{dst_info.get('name')}`")

    # ------------------ GOOGLE MAPS STYLE MAP ------------------
    st.markdown("---")
    st.subheader(f"Google Maps Traffic Heatmap (+{horizon_min} min Forecast)")

    # Color legend
    leg_col1, leg_col2, leg_col3, leg_col4 = st.columns(4)
    leg_col1.markdown("🟢 **Green**: Free Flow (Speed Ratio > 0.8)")
    leg_col2.markdown("🟡 **Yellow**: Moderate Traffic (Ratio 0.6 - 0.8)")
    leg_col3.markdown("🟠 **Orange**: Heavy Traffic (Ratio 0.4 - 0.6)")
    leg_col4.markdown("🔴 **Red**: Standstill / Severe Congestion (Ratio < 0.4)")

    polyline = route_data.get("polyline", [])
    if polyline:
        mid_idx = len(polyline) // 2
        map_center = polyline[mid_idx]
        m = folium.Map(location=map_center, zoom_start=8, tiles="OpenStreetMap")

        # 1. Base route outline (dark casing for Google Maps look)
        folium.PolyLine(
            locations=polyline,
            color="#2c3e50",
            weight=8,
            opacity=0.5
        ).add_to(m)

        # 2. Render Google Maps Colored Road Segments
        if "Traffic Lines" in map_layer_style or "Both" in map_layer_style:
            for s in route_segments:
                sub_pts = s.get("sub_polyline", [])
                if len(sub_pts) >= 2:
                    folium.PolyLine(
                        locations=sub_pts,
                        color=s["color"],
                        weight=6,
                        opacity=0.95,
                        tooltip=f"Segment {s['segment_idx']} ({s['progress_pct']}%): {s['predicted_level']} Congestion ({s['current_speed']} km/h)"
                    ).add_to(m)

        # 3. Render Density Heatmap Layer if selected
        if "Heatmap" in map_layer_style or "Both" in map_layer_style:
            heat_data = []
            for s in route_segments:
                # Add midpoint and intermediate points weighted by congestion index
                sub_pts = s.get("sub_polyline", [])
                weight = float(s["predicted_index"])
                for pt in sub_pts[::max(1, len(sub_pts) // 3)]:
                    heat_data.append([pt[0], pt[1], weight])

            if heat_data:
                HeatMap(
                    heat_data,
                    radius=18,
                    blur=14,
                    max_zoom=13,
                    gradient={0.2: "#00c853", 0.5: "#ffd600", 0.75: "#ff6d00", 1.0: "#d50000"}
                ).add_to(m)

        # 4. Start & End Markers
        folium.Marker(
            location=polyline[0],
            icon=folium.Icon(color="green", icon="play", prefix="fa"),
            tooltip=f"Start: {src_info.get('name')}"
        ).add_to(m)

        folium.Marker(
            location=polyline[-1],
            icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa"),
            tooltip=f"Destination: {dst_info.get('name')}"
        ).add_to(m)

        # 5. Checkpoint nodes
        for s in route_segments:
            popup_html = (
                f"<b>Checkpoint {s['segment_idx']} ({s['progress_pct']}% Route)</b><br/>"
                f"Current Speed: {s['current_speed']} km/h (Free Flow: {s['free_flow_speed']} km/h)<br/>"
                f"Predicted Level: <b>{s['predicted_level']}</b><br/>"
                f"Congestion Index: {s['predicted_index']}"
            )
            folium.CircleMarker(
                location=[s["lat"], s["lon"]],
                radius=6,
                color="#000000",
                weight=1,
                fill=True,
                fill_color=s["color"],
                fill_opacity=1.0,
                popup=folium.Popup(popup_html, max_width=260)
            ).add_to(m)

        st_folium(m, width="100%", height=480)

    # ------------------ ROAD CONGESTION PROFILE & CHECKPOINTS ------------------
    st.markdown("---")
    st.subheader(f"Along-Route Traffic Progression (+{horizon_min} min)")

    col_t1, col_t2 = st.columns([3, 2])

    with col_t1:
        pct_labels = [f"{s['progress_pct']}% Route" for s in route_segments]
        pred_indices = [s["predicted_index"] for s in route_segments]
        marker_colors = [s["color"] for s in route_segments]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=pct_labels,
            y=pred_indices,
            marker_color=marker_colors,
            name="Congestion Index"
        ))

        fig.add_hrect(y0=0.0, y1=0.375, fillcolor="#00c853", opacity=0.08, line_width=0, annotation_text="Free Flow")
        fig.add_hrect(y0=0.375, y1=0.675, fillcolor="#ffd600", opacity=0.08, line_width=0, annotation_text="Moderate")
        fig.add_hrect(y0=0.675, y1=0.875, fillcolor="#ff6d00", opacity=0.08, line_width=0, annotation_text="Heavy")
        fig.add_hrect(y0=0.875, y1=1.0, fillcolor="#d50000", opacity=0.08, line_width=0, annotation_text="Standstill")

        fig.update_layout(
            title=f"Predicted Congestion Index (Source ➔ Destination)",
            xaxis_title="Journey Progress Along Route",
            yaxis_title="Congestion Index (0.0 to 1.0)",
            yaxis=dict(range=[0.0, 1.05]),
            margin=dict(l=40, r=20, t=50, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_t2:
        st.markdown("##### Road Segment Congestion Table")
        table_rows = []
        for s in route_segments:
            table_rows.append({
                "Segment": f"Seg {s['segment_idx']} ({s['progress_pct']}%)",
                "Speed": f"{s['current_speed']} km/h",
                "Speed Ratio": f"{s['current_ratio']:.2f}",
                "Predicted Level": s["predicted_level"],
                "Index": f"{s['predicted_index']:.2f}"
            })
        st.dataframe(pd.DataFrame(table_rows), hide_index=True, use_container_width=True)
=======
import streamlit as st
import plotly.express as px
import pandas as pd
from typing import Dict, Any

from src.bottlenecks import find_network_bottlenecks


def render_feature4_tab(meta: Dict[str, Any]):
    st.header("🚨 Feature 4: Congestion Bottleneck Finder")
    st.caption("Automatically monitors and ranks road segments across Mumbai & Thane based on current traffic slowdown and predicted deterioration.")

    col_ctrl1, col_ctrl2 = st.columns([2, 2])
    with col_ctrl1:
        top_n = st.selectbox("Display Top N Bottlenecks", options=[5, 10, 15, 31], index=1)
    with col_ctrl2:
        st.write("")
        st.caption("ℹ️ Multi-factor score incorporates 50% current speed loss, 35% 30-min projected index, and 15% rate of deterioration.")

    bottlenecks = find_network_bottlenecks(meta=meta, top_n=top_n)

    # Top 3 High-Priority Callout Cards
    st.markdown("### 🔥 Top 3 Critical Corridor Choke Points")
    top3_cols = st.columns(3)
    for idx in range(min(3, len(bottlenecks))):
        b = bottlenecks[idx]
        with top3_cols[idx]:
            st.markdown(
                f"""
                <div style="background-color: {b['badge_color']}15; border-left: 5px solid {b['badge_color']}; padding: 14px; border-radius: 6px; margin-bottom: 10px;">
                    <span style="font-weight: bold; color: {b['badge_color']}; font-size: 1.1rem;">#{b['rank']} {b['name']}</span><br/>
                    <small style="color: #666;">Zone: {b['zone']} | {b['road_type']}</small>
                    <div style="margin-top: 8px; font-size: 0.9rem;">
                        <b>Score: {b['bottleneck_score']:.1f}/100</b> ({b['severity']})<br/>
                        Speed: <b>{b['current_speed']} km/h</b> (Limit: {b['speed_limit']} km/h | -{b['slowdown_pct']}%)<br/>
                        Est. Queue: <b>{b['queue_meters']} m</b> | 30m Δ: <b>{b['deterioration_delta']:+.2f}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("---")

    col_chart, col_tbl = st.columns([3, 3])
    with col_chart:
        st.subheader("📊 Ranked Bottleneck Severity Scores")
        df_chart = pd.DataFrame(bottlenecks).sort_values("bottleneck_score", ascending=True)
        fig_bar = px.bar(
            df_chart,
            x="bottleneck_score",
            y="name",
            orientation="h",
            color="bottleneck_score",
            color_continuous_scale="Reds",
            labels={"bottleneck_score": "Bottleneck Score (0–100)", "name": ""},
            height=380
        )
        fig_bar.update_layout(margin=dict(l=20, r=20, t=20, b=20), yaxis_title="")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_tbl:
        st.subheader("📋 Complete Bottleneck Prioritization Table")
        df_table = pd.DataFrame({
            "Rank": [f"#{b['rank']}" for b in bottlenecks],
            "Junction / Corridor": [b["name"] for b in bottlenecks],
            "Score": [f"{b['bottleneck_score']:.1f}" for b in bottlenecks],
            "Speed": [f"{b['current_speed']}/{b['speed_limit']} km/h" for b in bottlenecks],
            "Slowdown": [f"-{b['slowdown_pct']:.0f}%" for b in bottlenecks],
            "Queue": [f"{b['queue_meters']} m" for b in bottlenecks],
            "Status": [b["severity"] for b in bottlenecks]
        })
        st.dataframe(df_table, use_container_width=True, hide_index=True)
>>>>>>> e809fb07cd44c9b807ba2731379e2fc01fec6502
