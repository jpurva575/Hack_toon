import json
import logging
from pathlib import Path
import streamlit as st
import joblib

from src.config import MODEL_PATH, META_PATH
from src.ui_f1 import render_feature1_tab
from src.ui_f2 import render_feature2_tab
from src.ui_f3 import render_feature3_tab
from src.ui_f4 import render_feature4_tab
from src.ui_f5 import render_feature5_tab
from src.train import train_mumbai_thane_model

st.set_page_config(
    page_title="Mumbai-Thane Traffic Intelligence Suite (5 Features)",
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
        margin-bottom: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def load_artifacts():
    """Loads trained model and metadata."""
    if not MODEL_PATH.exists() or not META_PATH.exists():
        with st.spinner("Model artifacts not found. Training model pipeline now..."):
            meta = train_mumbai_thane_model()
            model = joblib.load(MODEL_PATH)
            return model, meta
            
    model = joblib.load(MODEL_PATH)
    with open(META_PATH, "r") as f:
        meta = json.load(f)
    return model, meta


def main():
    st.markdown('<div class="main-title">🚦 Mumbai-Thane Traffic Congestion Intelligence Suite</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">5 Integrated Predictive & Decision Engines (Pattern Insights, 5–120m Blend, Delay Estimator, Bottleneck Finder, Route Comparison & Alerts)</div>', unsafe_allow_html=True)

    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ System Control")
        st.info(
            """
            **5 Integrated Features:**
            1. **Pattern Insights & Classifier:** Macro-F1 0.926 vs Baseline 0.614
            2. **Live 5–120m Forecasting:** Exponential decay blend (tau = 60m)
            3. **Traffic Impact & Delay Estimator:** Free-flow vs actual delay & TTI
            4. **Congestion Bottleneck Finder:** Network ranking & deterioration
            5. **Route Comparison & Alerts:** Side-by-side corridors & warnings
            """
        )
        if st.button("🔁 Retrain Model Pipeline"):
            with st.spinner("Retraining model on Mumbai-Thane dataset..."):
                st.cache_resource.clear()
                train_mumbai_thane_model()
                st.success("Model successfully retrained and cached!")
                st.rerun()

        st.markdown("---")
        st.markdown("### 📋 GitHub Handover Guide")
        st.markdown(
            """
            - **All 31 Corridors:** Live speed stream + Open-Meteo weather
            - **Unit Tests:** `python -m unittest tests.test_all_features`
            - **Run Command:** `streamlit run app.py`
            """
        )
        st.caption("Mumbai-Thane Urban Traffic System | Production Ready")

    # Load artifacts
    try:
        model, meta = load_artifacts()
    except Exception as e:
        st.error(f"Failed to load model artifacts: {e}")
        return

    # 5 Feature Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 1. Pattern Insights",
        "⚡ 2. Live 5–120m Forecast",
        "⏱️ 3. Delay & Impact",
        "🚨 4. Bottleneck Finder",
        "🛣️ 5. Route Comparison & Alerts"
    ])

    with tab1:
        render_feature1_tab(model, meta)

    with tab2:
        render_feature2_tab(meta)

    with tab3:
        render_feature3_tab(meta)

    with tab4:
        render_feature4_tab(meta)

    with tab5:
        render_feature5_tab(meta)


if __name__ == "__main__":
    main()
