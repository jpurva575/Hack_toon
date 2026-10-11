import unittest
import datetime
import math
import joblib
import json

from src.config import (
    MODEL_PATH,
    META_PATH,
    DEFAULT_TAU,
    EXPECTED_WEIGHTS_TAU_60,
    NODES_CONFIG,
    ROUTES_CONFIG
)
from src.blend import compute_decay_weight, index_to_level, forecast_horizons
from src.live import speed_ratio_to_level, level_to_midpoint_index
from src.profile import get_profile_index_at_time, predict_node_level
from src.delay import estimate_segment_delay
from src.bottlenecks import find_network_bottlenecks
from src.routes import compare_route_pair, compute_route_metrics
from src.alerts import evaluate_congestion_alerts


class TestTraffic5Features(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Loads trained model and metadata once for test suite."""
        cls.model = joblib.load(MODEL_PATH)
        with open(META_PATH, "r") as f:
            cls.meta = json.load(f)

    # =========================================================================
    # FEATURE 1: Pattern Insights & Model Classification Tests
    # =========================================================================
    def test_feature1_model_prediction(self):
        """Tests that Feature 1 model outputs valid congestion levels and probabilities."""
        now = datetime.datetime(2026, 7, 10, 9, 0, 0)
        lvl, probs, X_single = predict_node_level("MUM_BKC_01", now, self.model, self.meta)
        
        self.assertIn(lvl, ["Low", "Moderate", "High", "Severe"])
        self.assertEqual(len(probs), 4)
        self.assertAlmostEqual(sum(probs), 1.0, places=3)
        self.assertEqual(len(X_single.columns), 15)

    def test_feature1_profile_subhour_interpolation(self):
        """Tests that profile index interpolates smoothly between adjacent hours."""
        dt_hour = datetime.datetime(2026, 7, 10, 8, 0, 0)
        dt_sub = datetime.datetime(2026, 7, 10, 8, 30, 0)
        dt_next = datetime.datetime(2026, 7, 10, 9, 0, 0)
        
        idx_h = get_profile_index_at_time(dt_hour, self.meta, "MUM_BKC_01")
        idx_sub = get_profile_index_at_time(dt_sub, self.meta, "MUM_BKC_01")
        idx_next = get_profile_index_at_time(dt_next, self.meta, "MUM_BKC_01")
        
        expected_sub = (idx_h + idx_next) / 2.0
        self.assertAlmostEqual(idx_sub, expected_sub, places=3)

    # =========================================================================
    # FEATURE 2: Live Integration & 5-120m Forecasting Tests
    # =========================================================================
    def test_feature2_decay_weights(self):
        """Verifies exponential weights w(h) = exp(-h / 60) match architecture spec."""
        for h, expected_w in EXPECTED_WEIGHTS_TAU_60.items():
            actual_w = round(compute_decay_weight(h, DEFAULT_TAU), 2)
            self.assertEqual(actual_w, expected_w, f"Horizon {h} min expected {expected_w}, got {actual_w}")

    def test_feature2_forecast_clipping_and_decay(self):
        """Verifies 7 horizons are generated and live weight decays from 5m to 120m."""
        now = datetime.datetime.now()
        fcasts = forecast_horizons(now, live_index=0.95, meta=self.meta)
        
        self.assertEqual(len(fcasts), 7)
        self.assertGreater(fcasts[0]["weight_live"], fcasts[-1]["weight_live"])
        self.assertEqual(fcasts[0]["horizon_min"], 5)
        self.assertEqual(fcasts[-1]["horizon_min"], 120)
        for f in fcasts:
            self.assertTrue(0.0 <= f["blended_index"] <= 1.0)

    def test_feature2_sensitivity_criteria(self):
        """PRD Acceptance Check: speed ratio change from 0.9 to 0.3 changes 5m forecast level."""
        now = datetime.datetime(2026, 7, 10, 8, 0, 0)
        idx_09 = level_to_midpoint_index(speed_ratio_to_level(0.9))
        idx_03 = level_to_midpoint_index(speed_ratio_to_level(0.3))
        
        f_09 = forecast_horizons(now, live_index=idx_09, meta=self.meta)
        f_03 = forecast_horizons(now, live_index=idx_03, meta=self.meta)
        
        self.assertNotEqual(f_09[0]["predicted_level"], f_03[0]["predicted_level"])
        self.assertEqual(f_09[0]["predicted_level"], "Low")
        self.assertIn(f_03[0]["predicted_level"], ["High", "Severe"])

    # =========================================================================
    # FEATURE 3: Traffic Impact & Delay Estimator Tests
    # =========================================================================
    def test_feature3_delay_estimation_math(self):
        """Verifies free-flow time, current travel time, delay, and TTI calculations."""
        node_id = "MUM_BKC_01"  # 3.2 km, 60 km/h limit -> 3.2 min free flow
        current_speed = 30.0    # 3.2 km at 30 km/h -> 6.4 min
        
        impact = estimate_segment_delay(node_id, current_speed=current_speed)
        
        self.assertAlmostEqual(impact["free_flow_time_min"], 3.2, places=1)
        self.assertAlmostEqual(impact["current_time_min"], 6.4, places=1)
        self.assertAlmostEqual(impact["current_delay_min"], 3.2, places=1)
        self.assertAlmostEqual(impact["current_tti"], 2.0, places=1)
        self.assertAlmostEqual(impact["speed_drop_pct"], 50.0, places=1)

    # =========================================================================
    # FEATURE 4: Congestion Bottleneck Finder Tests
    # =========================================================================
    def test_feature4_bottleneck_ranking(self):
        """Tests that bottlenecks are ranked correctly across network segments."""
        ranked = find_network_bottlenecks(self.meta, top_n=5)
        
        self.assertEqual(len(ranked), 5)
        # Scores must be descending
        for i in range(len(ranked) - 1):
            self.assertGreaterEqual(ranked[i]["bottleneck_score"], ranked[i+1]["bottleneck_score"])
            self.assertTrue(0.0 <= ranked[i]["bottleneck_score"] <= 100.0)

    # =========================================================================
    # FEATURE 5: Route Comparison & Proactive Alerts Tests
    # =========================================================================
    def test_feature5_route_comparison(self):
        """Tests corridor comparison between Route A and Route B with recommendation."""
        res = compare_route_pair("ROUTE_PAIR_1", meta=self.meta, departure_horizon=0)
        
        self.assertIn("route_a_name", res)
        self.assertIn("route_b_name", res)
        self.assertGreater(res["effective_time_a"], 0.0)
        self.assertGreater(res["effective_time_b"], 0.0)
        self.assertIn(res["recommended_route"], [res["route_a_name"], res["route_b_name"], "Either (Equivalent)"])

    def test_feature5_alert_triggers(self):
        """Tests that severe congestion triggers CRITICAL alert while clear traffic gives NORMAL."""
        now = datetime.datetime.now()
        # Simulated severe traffic
        severe_fcasts = forecast_horizons(now, live_index=0.95, meta=self.meta)
        alert_severe = evaluate_congestion_alerts("EEH Chembur", severe_fcasts, delay_threshold_min=10.0)
        self.assertTrue(alert_severe["has_alert"])
        self.assertIn(alert_severe["severity"], ["CRITICAL", "WARNING"])

        # Simulated clear traffic
        clear_fcasts = forecast_horizons(now, live_index=0.20, meta=self.meta)
        alert_clear = evaluate_congestion_alerts("EEH Chembur", clear_fcasts, delay_threshold_min=20.0)
        self.assertFalse(alert_clear["has_alert"])
        self.assertEqual(alert_clear["severity"], "NORMAL")


if __name__ == "__main__":
    unittest.main()
