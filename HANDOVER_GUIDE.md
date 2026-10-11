# TEAMMATE INTEGRATION GUIDE: Features 1-2 & 3-4

## 1. Quick Start Commands

### Run the Background Logger
Logs live traffic flow and weather every 300 seconds to `data/live_log.csv`:
```bash
python scripts/log_live.py
```
*(Or run single cycle: `python scripts/log_live.py --once`)*

### Run Cross-Region Calibration (Feature 3)
Reads `data/live_log.csv`, performs 70/30 chronological split per region, calculates regional offsets, and evaluates MAE / accuracy before and after:
```bash
python src/calibrate.py
```
**Artifacts Generated:**
- `models/calibration.json`: Per-region offsets and metrics.
- `data/calibration_report.csv`: Tabular evaluation report.

### Run Central Dashboard (Feature 4)
Launches the full interactive Streamlit operations dashboard:
```bash
python -m streamlit run app.py
```
*(Alternatively, if `streamlit` is in your PATH: `streamlit run app.py`)*

---

## 2. Pan-India Routing & Along-Route Traffic Prediction

The system is now pan-India enabled:
- Users input any **Source** and **Destination** in India (e.g. `Bandra, Mumbai` to `Koregaon Park, Pune`, or `Connaught Place, Delhi` to `Cyber Hub, Gurugram`).
- TomTom Search/Geocoding API resolves coordinates anywhere in India.
- TomTom Routing API computes the complete driving path.
- The route polyline is drawn on the map, with checkpoints sampled along the journey.
- The ML model + blend engine forecasts future traffic congestion for each checkpoint at horizons (+15m, +30m, +45m, +60m, +90m, +120m).
- Checkpoints are color-coded (🟢 Low, 🟡 Moderate, 🟠 High, 🔴 Severe).

---

## 3. Shared Interface Contract with Features 1 & 2

### How Feature 2 connects to Feature 3 & Routing:
In `src/blend.py` and `src/routing.py`, the model prediction functions (`predict_profile()` and `forecast()`) receive time and weather inputs to evaluate congestion index [0, 1].
- When your teammate updates `models/model.joblib` or `models/meta.json`, `src/profile.py` automatically reads the updated hourly profile and importances.
- If no trained model file is found yet, the system seamlessly falls back to the diurnal traffic profile without crashing.

---

## 3. Automated Test Verification
Run the unit test suite to verify time splitting, offset bounds, and sample threshold logic:
```bash
python -m unittest tests/test_calibrate.py
```
*(All 3 tests pass: split chronological order, conversion midpoints, <20 rows check).*
