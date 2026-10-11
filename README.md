# Mumbai-Thane Traffic Congestion Intelligence Suite (5 Features)

A production-ready, fully integrated traffic predictive intelligence and decision system built on the **Mumbai-Thane Historical Traffic Dataset** (33,480 hourly records across 31 key arterial corridors).

---

## 1. System Architecture & 5-Feature Suite

```
[Mumbai-Thane Dataset: 31 Nodes, 33,480 Rows]
                      │
                      ▼
 ┌─────────────────────────────────────────────────────────┐
 │ 1. Pattern Insights & ML Classifier                     │
 │    (HistGradientBoosting: Macro-F1 0.926 vs Base 0.614) │
 └────────────────────────────┬────────────────────────────┘
                              │
  [TomTom Speed / Fallback]   │   [Open-Meteo Weather]
              │               │               │
              ▼               ▼               ▼
 ┌─────────────────────────────────────────────────────────┐
 │ 2. Live Integration & 5–120 min Exponential Decay Blend │
 │    (Horizons: 5, 10, 15, 30, 60, 90, 120 min | tau=60m) │
 └────────────────────────────┬────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
 ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
 │ 3. Delay &   │      │ 4. Bottleneck│      │ 5. Route     │
 │    Impact    │      │    Finder    │      │    Compare & │
 │    Estimator │      │    (Ranking) │      │    Alerts    │
 └──────────────┘      └──────────────┘      └──────────────┘
```

### The 5 Integrated Features
1. **Feature 1: Pattern-Based Traffic Insights Module & Classifier**
   - Learns diurnal cycles, weekly recurring curves, and impact of local disruptions (waterlogging, metro construction, VIP morchas, vehicle breakdowns).
   - Classifies congestion into `Low`, `Moderate`, `High`, and `Severe`.
2. **Feature 2: Live Integration & 5–120 min Forecasting**
   - Ingests real-time road speeds and local weather; blends observations with historical profiles via exponential decay $w(h) = \exp(-h / 60)$.
   - Interactive live speed ratio simulator ($0.10$ to $1.00$) for instantaneous sensitivity testing.
3. **Feature 3: Traffic Impact and Delay Estimator**
   - Quantifies the exact commuter travel penalty by comparing free-flow baseline with current and projected travel times across horizons.
   - Computes added delay (min), speed loss %, Travel Time Index (TTI), and commuter departure advice.
4. **Feature 4: Congestion Bottleneck Finder**
   - Cross-evaluates all 31 corridors simultaneously using a composite prioritization score (50% current speed loss, 35% 30-min forecast index, 15% rate of deterioration $\Delta \text{index}$).
   - Estimates vehicle queue lengths (meters) and categorizes severity tiers (`Critical Choke Point`, `Active Bottleneck`, etc.).
5. **Feature 5: Route Comparison & Proactive Congestion Alerts**
   - Compares parallel corridors side-by-side (e.g. Eastern Express Highway vs. LBS Marg for Thane $\leftrightarrow$ South Mumbai) for departure windows (`Now`, `+15m`, `+30m`, `+60m`).
   - Active surveillance alert engine triggering advance warnings when predicted levels reach High/Severe or delay breaches user thresholds.

---

## 2. Model Performance & Evaluation Benchmark

Trained and evaluated on the chronological held-out 20% test split (June 1 – July 6 train, July 7 – July 15 test):

| Metric | Hour-of-Week Mode Baseline | Trained Gradient Boosting Model | Improvement |
|---|---|---|---|
| **Macro-F1 Score** | **0.6141** | **0.9261** | **+31.21%** |
| **Accuracy** | 71.4% | **95.37%** | **+23.97%** |
| **Low F1** | 0.812 | **0.981** | +16.9% |
| **Moderate F1** | 0.548 | **0.902** | +35.4% |
| **High F1** | 0.631 | **0.940** | +30.9% |
| **Severe F1** | 0.465 | **0.881** | +41.6% |

---

## 3. Quick Start & Execution

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run All Unit Tests (13 Tests Covering All 5 Features)
```bash
python -m unittest discover tests
```

### 3. Launch the 5-Feature Streamlit Web Application
```bash
streamlit run app.py
```

### 4. (Optional) Retrain Model Pipeline
```bash
python -m src.train
```

---

## 4. Repository Structure

```
traffic_congestion/
├── app.py                      # Main entry point with tabs for all 5 features
├── requirements.txt            # Dependency manifest
├── .gitignore                  # Git hygiene (ignoring caches & logs)
├── .env.example                # Optional TomTom API key template
├── README.md                   # Complete system documentation
├── PRD_WOW.md                  # PRD for Route Comparison & Alerts
├── ARCHITECTURE_WOW.md         # Architecture for Route Comparison & Alerts
├── data/
│   ├── mumbai_thane_traffic_historical.csv  # 33,480 records across 31 nodes
│   ├── sample_live.json        # Verified 31-node benchmark fallback
│   └── raw/traffic.csv         # Original reference dataset
├── models/
│   ├── mumbai_thane_model.joblib # Trained classifier
│   └── mumbai_thane_meta.json    # Profiles, feature importances, cutoffs
├── src/
│   ├── config.py               # 31 node coordinates, route pairs, constants
│   ├── features.py             # Feature engineering, per-node lags, proxies
│   ├── train.py                # Chronological split training & F1 benchmarks
│   ├── profile.py              # Sub-hour linear profile interpolation
│   ├── live.py                 # TomTom speed & Open-Meteo weather integrations
│   ├── blend.py                # 7-horizon decay blending engine (tau = 60m)
│   ├── delay.py                # Feature 3: Travel time delay & TTI estimator
│   ├── bottlenecks.py          # Feature 4: Network bottleneck ranking & queue
│   ├── routes.py               # Feature 5: Multi-segment corridor comparison
│   ├── alerts.py               # Feature 5: Proactive horizon warning triggers
│   ├── ui_f1.py                # UI Tab 1: Pattern Insights
│   ├── ui_f2.py                # UI Tab 2: Live 5-120m Forecasting
│   ├── ui_f3.py                # UI Tab 3: Delay & Impact Estimator
│   ├── ui_f4.py                # UI Tab 4: Bottleneck Finder
│   └── ui_f5.py                # UI Tab 5: Route Comparison & Alerts
├── scripts/
│   └── log_live.py             # Periodic background live logger
└── tests/
    ├── test_all_features.py    # Unit tests for all 5 features
    └── test_blend.py           # Unit tests for decay weights and thresholds
```

---

## 5. GitHub Push Instructions

To push the entire repository to GitHub:

```bash
git add .
git commit -m "feat: complete production-ready 5-feature traffic intelligence suite with Mumbai-Thane dataset"
git push origin main
```
