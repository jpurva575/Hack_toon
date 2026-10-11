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
