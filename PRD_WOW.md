# PRD_WOW: Congestion Alert System & Route Comparison System

Assumption: Built in a 6-hour hackathon on top of the 4 core features using existing Python, Streamlit, and dataset corridors.

## 1. Gap
Existing navigation apps only show congestion when drivers are already stuck in traffic, and existing models predict segment scores in isolation without active warnings. Commuters must manually check multiple road points to decide when to leave or which path to choose. The two WOW features turn passive segment predictions into active advance warnings and side-by-side corridor trade-offs.

## 2. Features

### WOW Feature 1: Congestion Alert System
- **WHY:** Users cannot constantly monitor numbers on a dashboard; they need an explicit, rule-based trigger that flags when a monitored road will enter High or Severe congestion in advance.
- **WHO:** Commuters planning departures and traffic operators managing corridor interventions.
- **WHAT:** Monitors selected corridors and evaluates predicted congestion across 5–120 min horizons. If predicted congestion level reaches Severe (or High if user-selected) or predicted extra delay exceeds a set threshold (e.g., >15 min), it generates a visual high-priority alert card with horizon time and severity level.
- **Acceptance check:** Selecting a congested road (e.g. EEH Chembur or simulated ratio 0.30) displays an active alert card specifying the horizon (e.g. "+15 min: Severe congestion alert"), whereas a clear road (ratio 0.90) displays "Normal Flow - No Active Alerts".
- **Build time in minutes:** 45 min.

### WOW Feature 2: Route Comparison System
- **WHY:** Single-segment forecasts tell a user how bad one road is, but do not answer whether an alternate corridor is faster right now or 30 minutes from now.
- **WHO:** Daily commuters choosing between parallel arterial routes (e.g., Eastern Express Highway vs LBS Marg, or WEH vs SV Road).
- **WHAT:** Compares two pre-configured alternative routes side-by-side across distance, free-flow time, current travel time, predicted travel time at +15/+30/+60 min, and bottleneck risk, recommending the optimal route.
- **Acceptance check:** Selecting origin-destination pair "Thane to South Mumbai" displays Route A (EEH) and Route B (LBS Marg) with comparative travel times, delta delay minutes, and highlights the faster route for the chosen departure horizon.
- **Build time in minutes:** 50 min.

## 3. Connection

### WOW Feature 1: Congestion Alert System
- **Link to Feature 1 (Pattern Learning & Congestion Classifier):** Uses historical baseline profiles to identify whether the alert is a routine rush-hour surge or an abnormal spike.
- **Link to Feature 2 (Live Integration & 5–120 min Forecasting):** Reads the 7 predicted horizon levels (5–120 min) to trigger advance warnings before peak congestion arrives.
- **Link to Feature 3 (Traffic Impact and Delay Estimator):** Evaluates estimated delay minutes against the user's alert threshold (e.g., trigger alert if delay > 15 min).
- **Link to Feature 4 (Congestion Bottleneck Finder):** Pulls the segment's bottleneck severity score to flag whether the alert is caused by a localized choke point.

### WOW Feature 2: Route Comparison System
- **Link to Feature 1 (Pattern Learning & Congestion Classifier):** Uses the historical weekday-vs-weekend pattern to show why a route typically slows down at that hour.
- **Link to Feature 2 (Live Integration & 5–120 min Forecasting):** Blends live speed and profile forecasts to calculate future travel time for each route at +15, +30, and +60 min.
- **Link to Feature 3 (Traffic Impact and Delay Estimator):** Sums the free-flow time and predicted congestion delay across segments to compute total estimated travel time per route.
- **Link to Feature 4 (Congestion Bottleneck Finder):** Identifies and displays the worst bottleneck segment along each route so users know where slowdowns will occur.

## 4. Demo Moment

- **WOW Feature 1 (1:15–1:35 of 2-min demo):** In Tab 2, toggle simulated speed ratio to 0.30; an alert banner immediately flashes: "CRITICAL ALERT: Severe congestion predicted in next 15–30 min (+18 min delay)". Judges notice immediate proactive warning without manual calculation.
- **WOW Feature 2 (1:35–1:55 of 2-min demo):** Switch to Route Comparison view. Compare "EEH Corridor" vs "LBS Marg Corridor". Show that while Route A is congested right now, Route B will worsen in 30 min, producing an automated recommendation card. Judges notice practical commuter decision value.

## 5. Out of scope

- Push notifications via SMS, WhatsApp, or mobile OS notifications (in-app Streamlit visual alert banners only).
- Dynamic GPS turn-by-turn routing, polyline map generation, or arbitrary coordinate pathfinding (pre-configured corridor pairs only).
- Live user vehicle tracking or crowdsourced incident reporting.
- Multi-modal transit comparisons (trains, metro, walking).
- Machine learning training for route optimization beyond segment aggregations.
