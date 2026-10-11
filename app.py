import json
import logging
from pathlib import Path
import streamlit as st
import joblib

from src.config import MODEL_PATH, META_PATH
from src.ui_f1 import render_feature1_tab
from src.ui_f2 import render_feature2_tab
from src.ui_f4 import render_dashboard as render_feature4_tab
from src.train import train_pipeline

st.set_page_config(
    page_title="Traffic Congestion Forecasting & Pan-India Route Engine",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom header styling
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
    st.markdown('<div class="main-title">🚦 Traffic Congestion Forecasting & Navigation Suite</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Complete 4-Feature Architecture: Pattern Learning (F1) + Live Decay Blending (F2) + Cross-Region Adaptation (F3) + Pan-India Route Heatmap (F4)</div>', unsafe_allow_html=True)

    # Load trained model and metadata
    try:
        model, meta = load_artifacts()
    except Exception as e:
        st.error(f"Failed to load model artifacts: {e}")
        return

    # Master Tab Navigation unifying Features 1, 2, 3 & 4
    tab_f4, tab_f2, tab_f1 = st.tabs([
        "🗺️ Feature 4 & 3: Pan-India Route Heatmap & Regional Forecast",
        "⚡ Feature 2: Live Integration & 5–120 min Forecast",
        "📊 Feature 1: Pattern Learning & Classifier"
    ])

    with tab_f4:
        render_feature4_tab()

    with tab_f2:
        render_feature2_tab(meta)

    with tab_f1:
        render_feature1_tab(model, meta)


if __name__ == "__main__":
    main()
