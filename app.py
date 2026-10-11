import json
import logging
from pathlib import Path
import streamlit as st
import joblib

from src.config import MODEL_PATH, META_PATH
from src.ui_f1 import render_feature1_tab
from src.ui_f2 import render_feature2_tab
from src.train import train_pipeline

st.set_page_config(
    page_title="Traffic Congestion Forecasting (5–120 min)",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom header CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a202c;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4a5568;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def load_artifacts():
    """Loads trained model and metadata."""
    if not MODEL_PATH.exists() or not META_PATH.exists():
        with st.spinner("Model artifacts not found. Training model pipeline now..."):
            meta = train_pipeline()
            model = joblib.load(MODEL_PATH)
            return model, meta
            
    model = joblib.load(MODEL_PATH)
    with open(META_PATH, "r") as f:
        meta = json.load(f)
    return model, meta


def main():
    st.markdown('<div class="main-title">🚦 Traffic Congestion Forecasting System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Dual-engine predictive architecture: Historical Pattern Classifier + Live Decay Blending (5–120 min)</div>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ System Control")
        st.info(
            """
            **Deliverables Built:**
            - **Feature 1:** Pattern Learning & Congestion Classifier (Macro-F1 0.838 vs Baseline 0.813)
            - **Feature 2:** Live Integration & 5–120 min Exponential Decay Blend (tau = 60m)
            """
        )
        if st.button("🔁 Retrain Feature 1 Model"):
            with st.spinner("Retraining model on historical dataset..."):
                st.cache_resource.clear()
                train_pipeline()
                st.success("Model successfully retrained and saved!")
                st.rerun()

        st.markdown("---")
        st.markdown("### 📋 Teammate Demo Guide (2 min)")
        st.markdown(
            """
            1. **Feature 1 Tab:** Show Monday 08:00 AM prediction, top drivers (Hour, Lags), and weekday vs weekend curves.
            2. **Feature 2 Tab:** Pick Mumbai corridor, click *Fetch Live Status*, inspect 7 forecast horizons.
            3. **Sensitivity Check:** Move *Simulate live speed ratio* to **0.30** $\\rightarrow$ see +5 min turn Severe while +120 min retains historical anchor.
            """
        )
        st.markdown("---")
        st.caption("Antigravity AI | Production Deliverable")

    # Load trained model and metadata
    try:
        model, meta = load_artifacts()
    except Exception as e:
        st.error(f"Failed to load model artifacts: {e}")
        return

    # Two main feature tabs matching PRD
    tab1, tab2 = st.tabs([
        "📊 Feature 1: Pattern Learning & Classifier",
        "⚡ Feature 2: Live Integration & 5–120 min Forecast"
    ])

    with tab1:
        render_feature1_tab(model, meta)

    with tab2:
        render_feature2_tab(meta)


if __name__ == "__main__":
    main()
