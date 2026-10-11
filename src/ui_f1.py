import datetime
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any

from src.config import LEVEL_COLORS, LEVEL_NAMES
from src.profile import build_single_row_features
from src.features import class_id_to_level


def render_feature1_tab(model, meta: Dict[str, Any]):
    st.header("🚦 Feature 1: Pattern Learning & Congestion Classifier")
    st.caption("Learns recurring traffic patterns from historical data and classifies congestion into 4 percentile-based tiers.")

    # Top KPI Metrics: Model Validation vs Baseline
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Model Macro-F1", f"{meta['model_f1']:.4f}")
    with col_m2:
        st.metric("Baseline Macro-F1", f"{meta['baseline_f1']:.4f}", help="Baseline predicts most frequent class for each hour-of-week")
    with col_m3:
        st.metric("Macro-F1 Gain", f"+{meta['f1_improvement_pct']:.2f}%", delta=f"{meta['f1_improvement_pct']:.2f}%")
    with col_m4:
        cutoffs = meta["cutoffs"]
        st.metric("Severe Cutoff (P90)", f"{cutoffs['P90']:.0f} veh/h")

    st.markdown("---")

    col_inputs, col_results = st.columns([1, 1])

    with col_inputs:
        st.subheader("📅 Target Date & Weather Conditions")
        selected_date = st.date_input("Date", value=datetime.date.today())
        selected_hour = st.slider("Hour of Day (0–23)", min_value=0, max_value=23, value=8)
        
        target_dt = datetime.datetime.combine(selected_date, datetime.time(selected_hour, 0))
        day_name = target_dt.strftime("%A")
        st.info(f"Selected Day: **{day_name}** | Target Timestamp: **{target_dt.strftime('%Y-%m-%d %H:00')}**")

        with st.expander("🌤️ Environmental Factors (Optional Overrides)", expanded=False):
            temp_c = st.slider("Temperature (°C)", min_value=-20.0, max_value=45.0, value=25.0, step=0.5)
            rain_mm = st.slider("Precipitation (mm/h)", min_value=0.0, max_value=50.0, value=0.0, step=0.5)
            clouds_pct = st.slider("Cloud Cover (%)", min_value=0, max_value=100, value=20, step=5)
            is_holiday = st.checkbox("Is Public Holiday / Festival", value=False)

    # Feature inference
    weather_dict = {"temp_c": temp_c, "rain_mm": rain_mm, "clouds_pct": clouds_pct}
    holiday_flag = 1 if is_holiday else 0
    features_df = build_single_row_features(target_dt, meta, weather_dict, holiday_flag)
    
    # Model prediction
    pred_class_id = int(model.predict(features_df)[0])
    pred_level = class_id_to_level(pred_class_id)
    pred_probs = model.predict_proba(features_df)[0]
    
    with col_results:
        st.subheader("🎯 Predicted Congestion Level")
        badge_color = LEVEL_COLORS.get(pred_level, "#6c757d")
        
        st.markdown(
            f"""
            <div style="background-color: {badge_color}22; border-left: 6px solid {badge_color}; padding: 18px; border-radius: 8px; margin-bottom: 12px;">
                <h2 style="color: {badge_color}; margin: 0; font-size: 2rem;">{pred_level} Congestion</h2>
                <p style="margin: 4px 0 0 0; color: #555; font-size: 0.95rem;">
                    Confidence: <b>{pred_probs[pred_class_id]*100:.1f}%</b> | 
                    Percentile Cutoffs: Low &lt; P40 ({cutoffs['P40']:.0f}), Mod P40–P70 ({cutoffs['P70']:.0f}), High P70–P90 ({cutoffs['P90']:.0f}), Severe &gt; P90
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Probabilities breakdown
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

    # Visualizations: Factors & Weekday vs Weekend Patterns
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("🔍 Top 5 Congestion Drivers (Feature Importance)")
        importances = meta.get("feature_importances", {})
        top5 = list(importances.items())[:5]
        top5_df = pd.DataFrame(top5, columns=["Factor", "Importance (%)"]).sort_values("Importance (%)", ascending=True)
        
        # Friendly factor names
        name_map = {
            "hour": "Hour of Day",
            "lag_24h": "Volume 24h Prior (Lag)",
            "day_of_week": "Day of Week",
            "lag_168h": "Volume 7d Prior (Lag)",
            "month": "Seasonal Month",
            "temp_c": "Temperature",
            "clouds_pct": "Cloud Cover",
            "rain_mm": "Rainfall",
            "is_weekend": "Weekend Flag",
            "holiday_flag": "Holiday Flag"
        }
        top5_df["Factor_Label"] = top5_df["Factor"].map(lambda x: name_map.get(x, x))
        
        fig_factors = px.bar(
            top5_df,
            x="Importance (%)",
            y="Factor_Label",
            orientation="h",
            color="Importance (%)",
            color_continuous_scale="Blues",
            text="Importance (%)",
            height=320
        )
        fig_factors.update_layout(margin=dict(l=20, r=20, t=20, b=20), showlegend=False, yaxis_title="")
        fig_factors.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_factors, use_container_width=True)

    with chart_col2:
        st.subheader("📈 Weekday vs Weekend Volume Curve")
        weekday_curve = meta.get("weekday_curve", [])
        weekend_curve = meta.get("weekend_curve", [])
        hours = list(range(24))
        
        fig_curve = go.Figure()
        fig_curve.add_trace(go.Scatter(
            x=hours,
            y=weekday_curve,
            mode="lines+markers",
            name="Weekday (Mon–Fri)",
            line=dict(color="#1f77b4", width=3)
        ))
        fig_curve.add_trace(go.Scatter(
            x=hours,
            y=weekend_curve,
            mode="lines+markers",
            name="Weekend (Sat–Sun)",
            line=dict(color="#ff7f0e", width=3, dash="dot")
        ))
        
        # Vertical marker for selected hour
        fig_curve.add_vline(
            x=selected_hour,
            line_width=2,
            line_dash="dash",
            line_color="#e377c2",
            annotation_text=f"Selected: {selected_hour}:00",
            annotation_position="top right"
        )
        
        fig_curve.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=320,
            xaxis=dict(title="Hour of Day", dtick=2),
            yaxis=dict(title="Average Volume (vehicles/h)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_curve, use_container_width=True)

    st.caption("ℹ️ **Modeling Note & Assumption:** For future dates/times without recorded real history, lag_24h and lag_168h use the hour-of-week average volume proxy.")
