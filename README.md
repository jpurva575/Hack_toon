# Traffic Congestion Forecasting System (5–120 min)

Dual-engine predictive traffic system built with **scikit-learn**, **Open-Meteo**, **TomTom API**, and **Streamlit**.

---

## 1. Overview & Architecture

The system resolves the fundamental limitation of short-term congestion planning: **historical datasets are hourly and static**, while **live APIs only capture the current instant**.

```
Historical CSV (Volume, Weather, Lags)
              │
              ▼
   [Feature 1: Pattern Learning] ──► models/model.joblib & meta.json (P40, P70, P90 cutoffs)
                                                      │
Live Traffic API (Current/Free-flow speed)            │
              │                                       ▼
              ├──► [Feature 2: Decay Blend] ◄─────────┘
              │           │
Live Weather ─┘           ▼
                  Forecast Horizons (5, 10, 15, 30, 60, 90, 120 min)
                  Live Weight w(h) = exp(-h / 60)
```

---

## 2. Mathematical Blending Formulation

$$\text{index}(h) = \text{profile}(\text{now} + h) + \left(\text{live\_index} - \text{profile}(\text{now})\right) \cdot w(h)$$

where:
- $w(h) = \exp(-h / \tau)$ with decay half-life $\tau = 60\text{ min}$.
- Sub-hour profile queries $\text{profile}(t)$ are calculated using linear interpolation between adjacent hourly points.

### Decay Weights Across Horizons ($\tau = 60\text{ min}$)
| Horizon ($h$) | Live Weight $w(h)$ | Historical Weight $(1 - w(h))$ | Dominant Factor |
|---|---|---|---|
| **5 min** | **92%** | 8% | Immediate road speed |
| **10 min** | **85%** | 15% | Live traffic dynamics |
| **15 min** | **78%** | 22% | Live traffic dynamics |
| **30 min** | **61%** | 39% | Transitional blend |
| **60 min** | **37%** | 63% | Recurring hourly pattern |
| **90 min** | **22%** | 78% | Recurring hourly pattern |
| **120 min** | **14%** | **86%** | Historical diurnal trend |

### Congestion Level Cutoffs
- **Volume Percentiles (Feature 1):**
  - **Low:** $< P_{40}$ ($< 2,783\text{ veh/h}$)
  - **Moderate:** $P_{40} - P_{70}$ ($2,783 - 4,741\text{ veh/h}$)
  - **High:** $P_{70} - P_{90}$ ($4,741 - 5,835\text{ veh/h}$)
  - **Severe:** $> P_{90}$ ($> 5,835\text{ veh/h}$)
- **Live Speed Ratio ($\text{ratio} = \frac{\text{currentSpeed}}{\text{freeFlowSpeed}}$):**
  - $> 0.80$: Low (midpoint index = 0.20)
  - $0.60 - 0.80$: Moderate (midpoint index = 0.55)
  - $0.40 - 0.60$: High (midpoint index = 0.80)
  - $< 0.40$: Severe (midpoint index = 0.95)

---

## 3. Directory Layout

```
traffic_congestion/
├── app.py                 # Streamlit entry point (Tab 1 & Tab 2)
├── requirements.txt       # Dependencies
├── .env.example           # Optional API key template
├── README.md              # Project handover guide
├── data/
│   ├── raw/traffic.csv    # Deduplicated historical dataset (UCI Metro Volume)
│   ├── processed/         # Engineered features (parquet)
│   ├── sample_live.json   # Verified sample fallback response
│   └── live_log.csv       # Background logged live readings
├── models/
│   ├── model.joblib       # Trained HistGradientBoostingClassifier
│   └── meta.json          # Cutoffs, profiles, F1 benchmarks, importances
├── src/
│   ├── config.py          # Coordinates, thresholds, constants
│   ├── features.py        # Data cleaning, lags, feature engineering
│   ├── train.py           # Training pipeline & macro-F1 benchmark
│   ├── profile.py         # Sub-hour profile interpolation & features
│   ├── live.py            # TomTom & Open-Meteo API integrations
│   ├── blend.py           # Exponential decay short-term forecast
│   ├── ui_f1.py           # Streamlit Tab 1 component
│   └── ui_f2.py           # Streamlit Tab 2 component
├── scripts/
│   └── log_live.py        # Optional background live logger
└── tests/
    └── test_blend.py      # Unit tests for blend & acceptance checks
```

---

## 4. Setup & Execution

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Tests
```bash
python -m unittest tests.test_blend
```
*(All 4 unit tests will verify weight decay, clipping, level thresholds, and sensitivity).*

### 3. Launch Streamlit Application
```bash
streamlit run app.py
```

### 4. (Optional) Retrain Model from Scratch
```bash
python -m src.train
```
Benchmark outputs on the last 20% held-out test split:
- **Baseline Macro-F1 (Hour-of-Week Mode):** `0.8134`
- **Model Macro-F1 (HistGradientBoosting):** `0.8375` (+2.42% gain)

---

## 5. Teammate Demo Walkthrough (2 Minutes)

1. **Problem Statement (0:00–0:15):** Explain that historical traffic data only knows general hourly patterns, while live navigation apps only know the current instant. We blend them mathematically.
2. **Tab 1: Pattern Learning & Classifier (0:15–0:45):**
   - Pick Monday 8:00 AM.
   - Show predicted level and confidence.
   - Point to the Top 5 Congestion Drivers (Hour of Day, 24h Lag, 7d Lag).
   - Show the Weekday vs. Weekend curve comparison.
3. **Tab 2: Live Integration & Forecasting (0:45–1:25):**
   - Pick the Mumbai corridor (Lat 19.0760, Lon 72.8777).
   - Click **Fetch Live Status** (queries live road speed and Open-Meteo weather).
   - Inspect the 7-horizon forecast badges from +5 min to +120 min.
4. **Weight Decay Proof (1:25–1:45):**
   - Examine the Weight Table: at +5 min, live road speed has **92%** control; at +120 min, historical pattern has **86%** control.
5. **Interactive Sensitivity Simulation (1:45–2:00):**
   - Slide the **Simulate live speed ratio** slider from `0.90` (smooth flow) down to `0.30` (severe incident).
   - Observe how the 5-min forecast immediately flips to High/Severe while the 120-min forecast remains anchored to the historical pattern.
   - Conclude with engineering boundaries (hourly historical baseline, sub-hour linear interpolation, and reference transfer to Indian road corridors).
