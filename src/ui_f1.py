import datetime
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any

from src.config import LEVEL_COLORS, LEVEL_NAMES, NODES_CONFIG
from src.profile import predict_node_level


def render_feature1_tab(model, meta: Dict[str, Any]):
    st.header("📊 Feature 1: Pattern-Based Traffic Insights & Classifier")
    st.caption("Learns recurring multi-week congestion patterns from the Mumbai-Thane network and predicts segment congestion levels.")

    # Top KPI Metrics: Validation vs Baseline on 20% Held-Out Chronological Split
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Model Macro-F1", f"{meta['model_f1']:.4f}")
    with c2:
        st.metric("Baseline Macro-F1", f"{meta['baseline_f1']:.4f}", help="Per-node hour-of-week mode baseline")
    with c3:
        st.metric("Macro-F1 Gain", f"+{meta['f1_improvement_pct']:.2f}%", delta=f"{meta['f1_improvement_pct']:.2f}%")
    with c4:
        st.metric("Total Corridor Nodes", f"{meta.get('total_nodes', 31)}")

    st.markdown("---")

    col_inputs, col_results = st.columns([1, 1])

    with col_inputs:
        st.subheader("📍 Junction Selection & Context")
        selected_node_id = st.selectbox(
            "Select Road Junction / Corridor",
            options=list(NODES_CONFIG.keys()),
            format_func=lambda x: f"{NODES_CONFIG[x]['name']} ({NODES_CONFIG[x]['zone']})",
            index=0
        )
        node_info = NODES_CONFIG[selected_node_id]
        st.info(f"🛣️ **{node_info['name']}** | {node_info['road_type']} | {node_info['lanes']} Lanes | Speed Limit: {node_info['speed_limit']} km/h")

        selected_date = st.date_input("Date", value=datetime.date.today(), key="f1_date")
        selected_hour = st.slider("Hour of Day (0–23)", min_value=0, max_value=23, value=9, key="f1_hour")
        target_dt = datetime.datetime.combine(selected_date, datetime.time(selected_hour, 0))

        with st.expander("🌦️ Weather & Local Mumbai Disruption Factors", expanded=True):
            waterlogging = st.slider("Waterlogging Index (0 = Dry, 1 = Deep Water)", min_value=0.0, max_value=1.0, value=0.0, step=0.05)
            rainfall = st.slider("Rainfall (mm/h)", min_value=0.0, max_value=80.0, value=0.0, step=1.0)
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                metro_work = st.checkbox("Metro Construction Active", value=False)
                vip_movement = st.checkbox("VIP Movement / Morcha", value=False)
            with col_d2:
                breakdown = st.checkbox("Vehicle Breakdown Reported", value=False)
                holiday = st.checkbox("Public Holiday / Festival", value=False)
            temp_c = st.slider("Temperature (°C)", min_value=20.0, max_value=42.0, value=30.0, step=0.5)

    weather_dict = {"temperature": temp_c, "rainfall_mm": rainfall, "air_quality_index": 120.0}
    disruptions = {
        "waterlogging_index": waterlogging,
        "metro_construction_work": 1 if metro_work else 0,
        "vip_movement_or_morcha": 1 if vip_movement else 0,
        "vehicle_breakdown_reported": 1 if breakdown else 0,
        "is_holiday_festival": 1 if holiday else 0
    }

    pred_level, pred_probs, _ = predict_node_level(selected_node_id, target_dt, model, meta, weather_dict, disruptions)

    with col_results:
        st.subheader("🎯 Predicted Congestion Level")
        badge_color = LEVEL_COLORS.get(pred_level, "#6c757d")
        
        st.markdown(
            f"""
            <div style="background-color: {badge_color}22; border-left: 6px solid {badge_color}; padding: 18px; border-radius: 8px; margin-bottom: 12px;">
                <h2 style="color: {badge_color}; margin: 0; font-size: 2rem;">{pred_level} Congestion</h2>
                <p style="margin: 4px 0 0 0; color: #555; font-size: 0.95rem;">
                    Target: <b>{target_dt.strftime('%A, %b %d at %H:00')}</b> | Segment: <b>{node_info['name']}</b>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        prob_df = pd.DataFrame({
            "Level": LEVEL_NAMES,
            "Probability (%)": [round(p * 100, 1) for p in pred_probs]
        })
        fig_prob = px.bar(
            prob_df,
            x="Level",
            y="Probability (%)",
            color="Level",
            color_discrete_map=LEVEL_COLORS,
            text="Probability (%)",
            height=200
        )
        fig_prob.update_layout(showlegend=False, margin=dict(l=20, r=20, t=10, b=20), yaxis_range=[0, 100])
        fig_prob.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_prob, use_container_width=True)

    st.markdown("---")

    # Factors & Curves
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("🔍 Key Model Drivers (Feature Importances)")
        importances = meta.get("feature_importances", {})
        top5 = list(importances.items())[:6]
        top5_df = pd.DataFrame(top5, columns=["Factor", "Importance (%)"]).sort_values("Importance (%)", ascending=True)
        
        friendly_names = {
            "lag_168h": "Volume 7d Prior (Weekly Pattern)",
            "waterlogging_index": "Waterlogging Severity",
            "lanes": "Corridor Lane Capacity",
            "hour": "Hour of Day (Diurnal Cycle)",
            "metro_construction_work": "Metro Construction Work",
            "lag_24h": "Volume 24h Prior (Daily Pattern)",
            "speed_limit": "Free-Flow Speed Limit",
            "rainfall_mm": "Rainfall Precipitation",
            "is_weekend": "Weekend vs Weekday",
            "vehicle_breakdown_reported": "Vehicle Breakdown"
        }
        top5_df["Factor_Label"] = top5_df["Factor"].map(lambda x: friendly_names.get(x, x))
        
        fig_factors = px.bar(
            top5_df,
            x="Importance (%)",
            y="Factor_Label",
            orientation="h",
            color="Importance (%)",
            color_continuous_scale="Blues",
            text="Importance (%)",
            height=300
        )
        fig_factors.update_layout(margin=dict(l=20, r=20, t=10, b=20), showlegend=False, yaxis_title="")
        fig_factors.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_factors, use_container_width=True)

    with chart_col2:
        st.subheader("📈 Weekday vs Weekend Volume Profile")
        weekday_curve = meta.get("weekday_curve", [])
        weekend_curve = meta.get("weekend_curve", [])
        hours = list(range(24))
        
        fig_curve = go.Figure()
        fig_curve.add_trace(go.Scatter(x=hours, y=weekday_curve, mode="lines+markers", name="Weekday (Mon–Fri)", line=dict(color="#1f77b4", width=3)))
        fig_curve.add_trace(go.Scatter(x=hours, y=weekend_curve, mode="lines+markers", name="Weekend (Sat–Sun)", line=dict(color="#ff7f0e", width=3, dash="dot")))
        fig_curve.add_vline(x=selected_hour, line_width=2, line_dash="dash", line_color="#e377c2", annotation_text=f"{selected_hour}:00", annotation_position="top right")
        fig_curve.update_layout(
            margin=dict(l=20, r=20, t=10, b=20),
            height=300,
            xaxis=dict(title="Hour of Day", dtick=2),
            yaxis=dict(title="Avg Vehicles / Hour"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_curve, use_container_width=True)
