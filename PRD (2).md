# PRD: Traffic Congestion Forecasting (5–120 min)

Assumptions (one line each):
- Only the 2 features below are built, because that is what was specified. Each has its own small Streamlit tab, so there is no separate dashboard feature.
- Users are taken from the PS: commuters and city traffic planners.
- The historical dataset is hourly. It is provided by the organizers; if not, the UCI "Metro Interstate Traffic Volume" dataset is the fallback (not verified, check columns first).

## 1. Problem
Traffic congestion changes with time, day, weather and holidays, so one fixed rule does not work. Historical datasets show the recurring patterns, but they are hourly, old, and from another city. Live traffic APIs show only the current moment, so neither source alone gives a usable short-term forecast.

## 2. Users
- **Commuters:** They check a map app for current traffic only. They cannot see whether it will get worse in the next 15–120 minutes, or why.
- **City traffic planners:** They see raw volumes or speeds with no simple Low/Moderate/High/Severe label, and no explanation of what drives congestion.

## 3. Goal
Classify traffic into 4 levels from historical patterns, and forecast it at 5, 10, 15, 30, 60, 90 and 120 minutes by blending those patterns with the live reading, showing how much weight each gets.

## 4. Features

### Feature 1: Pattern Learning & Congestion Classifier
- **WHY:** Users need to know what normal traffic looks like for a given time, and what drives it.
- **WHO:** Planners mainly; commuters for "is 8 AM Monday usually bad?".
- **WHAT:** Trains a model on time, day, weather, holiday and lag features. Labels traffic Low/Moderate/High/Severe, with levels defined by volume percentiles (our choice, stated in the UI). Outputs the hourly profile, the weekday-vs-weekend pattern, and feature importance as the "factors" view.
- **Acceptance check:** On a time-based held-out split (last 20% of the data), the model's macro-F1 is printed and beats a baseline that predicts the most common level for each hour-of-week. In the UI, picking any datetime shows a level, the top 5 factors, and the weekday-vs-weekend chart.
- **Build time:** 60 min

### Feature 2: Live Integration & 5–120 min Forecasting
- **WHY:** Users need a short-term forecast that reacts to what is happening on the road right now.
- **WHO:** Commuters mainly; planners for spotting deviations from normal.
- **WHAT:** Fetches current speed vs free-flow speed for a location from a public traffic API and converts it to a congestion level. Fetches current weather. Builds the forecast for all 7 horizons by blending the Feature 1 profile with the live deviation. Shows the live-vs-history weight at each horizon.
- **Acceptance check:** Changing the live speed ratio from 0.9 to 0.3 changes the 5-minute forecast level and the chart. The live weight at 5 min is greater than at 120 min, and the weights are displayed.
- **Build time:** 80 min

## 5. How the features connect
1. Feature 1 trains once and saves the model, the percentile thresholds and the hourly profile.
2. The user picks a location and time in the app.
3. Feature 2 fetches live speed and weather and turns them into a live congestion index.
4. Feature 2 loads Feature 1's profile for now and for each future horizon.
5. The blend is: forecast(h) = profile(now + h) + (live now − profile now) × weight(h). Weight starts high at 5 min and decays toward 120 min.
6. The result is mapped back to the 4 levels and shown with the weights. Feature 1's factors explain the historical part.

## 6. Demo flow (2 minutes)
1. **0:00–0:15:** State the problem in one sentence. History is hourly and live is a snapshot, so we blend them.
2. **0:15–0:45:** Open the Feature 1 tab. Pick Monday 8 AM. Show the level, the factors chart and the weekday-vs-weekend pattern. State that levels are percentile-based.
3. **0:45–1:25:** Open the Feature 2 tab. Pick a Mumbai point. Click Fetch live. Show the current level, the weather and the 7-horizon forecast chart.
4. **1:25–1:45:** Show the weight table. Point out that the 5-minute forecast follows live data and the 120-minute forecast follows history.
5. **1:45–2:00:** Move the "Simulate live speed ratio" slider (labelled as a simulation). The chart changes. Close with the limits: hourly history, a short live log, and no validation on Indian roads.

## 7. Out of scope
- Cross-region calibration and per-region accuracy evaluation. Live data works for any lat/lon, but only that part is built.
- Map view, heatmap, congestion alerts and route comparison.
- Transfer learning and fine-tuning.
- Deep learning and any model beyond scikit-learn.
- User accounts, a database, and deployment beyond running locally.
- Real 5/10/15-minute accuracy claims. These horizons are interpolated and live-driven, and are validated only as a proof of concept.
