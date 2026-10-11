import unittest
import datetime
import math
from src.config import EXPECTED_WEIGHTS_TAU_60, DEFAULT_TAU
from src.blend import (
    compute_decay_weight,
    index_to_level,
    forecast_horizons
)
from src.live import speed_ratio_to_level, level_to_midpoint_index


class TestTrafficBlend(unittest.TestCase):

    def test_decay_weights(self):
        """Verifies that exponential weights with tau=60 match the architecture specification."""
        for h, expected_w in EXPECTED_WEIGHTS_TAU_60.items():
            actual_w = round(compute_decay_weight(h, DEFAULT_TAU), 2)
            self.assertEqual(
                actual_w,
                expected_w,
                f"Horizon {h} min expected {expected_w}, got {actual_w}"
            )

    def test_index_to_level_mapping(self):
        """Verifies cutoff bands: <0.40 Low, 0.40-0.70 Moderate, 0.70-0.90 High, >0.90 Severe."""
        self.assertEqual(index_to_level(0.10), "Low")
        self.assertEqual(index_to_level(0.39), "Low")
        self.assertEqual(index_to_level(0.40), "Moderate")
        self.assertEqual(index_to_level(0.55), "Moderate")
        self.assertEqual(index_to_level(0.70), "Moderate")
        self.assertEqual(index_to_level(0.71), "High")
        self.assertEqual(index_to_level(0.85), "High")
        self.assertEqual(index_to_level(0.90), "High")
        self.assertEqual(index_to_level(0.91), "Severe")
        self.assertEqual(index_to_level(0.99), "Severe")

    def test_forecast_blend_clipping_and_decay(self):
        """Verifies that forecast values stay within [0, 1] and live weight decays toward 120 min."""
        dummy_meta = {
            "hourly_profile": {
                f"{dow}_{h}": {"volume": 3000, "index": 0.50, "level": "Moderate"}
                for dow in range(7) for h in range(24)
            }
        }
        now = datetime.datetime(2026, 10, 12, 8, 0, 0)
        
        forecasts = forecast_horizons(now, live_index=1.0, meta=dummy_meta)
        
        self.assertEqual(len(forecasts), 7)
        self.assertGreater(forecasts[0]["weight_live"], forecasts[-1]["weight_live"])
        self.assertEqual(forecasts[0]["horizon_min"], 5)
        self.assertEqual(forecasts[-1]["horizon_min"], 120)
        
        for f in forecasts:
            self.assertTrue(0.0 <= f["blended_index"] <= 1.0)

    def test_acceptance_criteria_speed_ratio_sensitivity(self):
        """
        Acceptance check from PRD:
        Changing the live speed ratio from 0.9 to 0.3 changes the 5-minute forecast level,
        and live weight at 5 min is greater than at 120 min.
        """
        dummy_meta = {
            "hourly_profile": {
                f"{dow}_{h}": {"volume": 3000, "index": 0.30, "level": "Low"}
                for dow in range(7) for h in range(24)
            }
        }
        now = datetime.datetime(2026, 10, 12, 8, 0, 0)
        
        # Ratio 0.9 -> Low level -> 0.20 index
        level_09 = speed_ratio_to_level(0.9)
        idx_09 = level_to_midpoint_index(level_09)
        forecast_09 = forecast_horizons(now, live_index=idx_09, meta=dummy_meta)
        
        # Ratio 0.3 -> Severe level -> 0.95 index
        level_03 = speed_ratio_to_level(0.3)
        idx_03 = level_to_midpoint_index(level_03)
        forecast_03 = forecast_horizons(now, live_index=idx_03, meta=dummy_meta)
        
        # 5 min forecast must change level
        self.assertNotEqual(forecast_09[0]["predicted_level"], forecast_03[0]["predicted_level"])
        self.assertEqual(forecast_09[0]["predicted_level"], "Low")
        self.assertIn(forecast_03[0]["predicted_level"], ["Severe", "High"])
        
        # Live weight at 5 min is greater than at 120 min
        self.assertGreater(forecast_03[0]["weight_live"], forecast_03[-1]["weight_live"])


if __name__ == "__main__":
    unittest.main()
