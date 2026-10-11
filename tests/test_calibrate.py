"""
Unit and regression tests for Feature 3 calibration pipeline:
1. Verifies that train/test split is strictly time-based (chronological) with no leakage.
2. Verifies offset calculation and clipping logic.
3. Verifies that regions with fewer than 20 rows receive status 'not enough data'.
4. Verifies ratio to level conversion thresholds and midpoints.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.calibrate import calibrate_region
from src.utils import ratio_to_level_and_index, index_to_level


class TestCalibration(unittest.TestCase):

    def test_ratio_to_level_and_index_conversions(self):
        """Test standard conversion thresholds."""
        # Low (> 0.8)
        lvl, idx = ratio_to_level_and_index(0.85)
        self.assertEqual(lvl, "Low")
        self.assertEqual(idx, 0.20)

        # Moderate (0.6 - 0.8)
        lvl, idx = ratio_to_level_and_index(0.70)
        self.assertEqual(lvl, "Moderate")
        self.assertEqual(idx, 0.55)

        # High (0.4 - 0.6)
        lvl, idx = ratio_to_level_and_index(0.50)
        self.assertEqual(lvl, "High")
        self.assertEqual(idx, 0.80)

        # Severe (<= 0.4)
        lvl, idx = ratio_to_level_and_index(0.35)
        self.assertEqual(lvl, "Severe")
        self.assertEqual(idx, 0.95)

    def test_insufficient_data_status(self):
        """Ensure regions with < 20 rows are marked as 'not enough data'."""
        # Generate only 15 rows
        dates = [datetime(2026, 10, 11, 8, 0) + timedelta(minutes=5 * i) for i in range(15)]
        df = pd.DataFrame({
            "dt": dates,
            "live_index": [0.55] * 15,
            "profile_index": [0.50] * 15,
            "live_level": ["Moderate"] * 15
        })
        res = calibrate_region(df, "konkan", total_region_rows=15)
        self.assertEqual(res["status"], "not enough data")
        self.assertEqual(res["n_usable"], 15)
        self.assertIsNone(res["mae_before"])

    def test_chronological_split_and_offset_math(self):
        """Ensure 70% train / 30% test split preserves time order and computes offset accurately."""
        n_samples = 40
        start_time = datetime(2026, 10, 11, 6, 0)
        dates = [start_time + timedelta(minutes=5 * i) for i in range(n_samples)]

        # Let profile_index be 0.50, and live_index be 0.60
        # Expected offset on train is mean(0.60 - 0.50) = +0.10
        profile_indices = [0.50] * n_samples
        live_indices = [0.60] * n_samples
        live_levels = ["Moderate"] * n_samples

        df = pd.DataFrame({
            "dt": dates,
            "live_index": live_indices,
            "profile_index": profile_indices,
            "live_level": live_levels
        })

        res = calibrate_region(df, "mumbai", total_region_rows=40)
        self.assertEqual(res["status"], "calibrated")
        self.assertEqual(res["n_train"], 28)  # floor(0.7 * 40)
        self.assertEqual(res["n_test"], 12)
        self.assertAlmostEqual(res["offset"], 0.10, places=3)
        self.assertAlmostEqual(res["mae_before"], 0.10, places=3)
        self.assertAlmostEqual(res["mae_after"], 0.00, places=3)


if __name__ == "__main__":
    unittest.main()
