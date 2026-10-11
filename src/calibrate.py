"""
Cross-Region Calibration Engine (Feature 3)
1. Loads data/live_log.csv (filtering api_ok == True).
2. Converts raw ratios into live index based on agreed midpoint conventions:
   Low: 0.20, Moderate: 0.55, High: 0.80, Severe: 0.95.
3. Computes model's baseline profile_index for each row (holiday forced to 0).
4. Splits chronologically per region: first 70% Train, last 30% Test.
5. Computes offset = mean(live_index - profile_index) on Train.
6. Evaluates test set before (profile_index) vs after (clip(profile_index + offset, 0, 1)):
   - MAE Before & MAE After
   - Discrete classification accuracy Before & After
7. If a region has fewer than 20 usable rows, outputs status: "not enough data".
8. Saves models/calibration.json and data/calibration_report.csv.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.config import REGIONS, MIN_CALIBRATION_SAMPLES
from src.utils import ratio_to_level_and_index, index_to_level
from src.profile import predict_profile

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

LOG_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "live_log.csv")
CALIBRATION_JSON_PATH = os.path.join(PROJECT_ROOT, "models", "calibration.json")
CALIBRATION_REPORT_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "calibration_report.csv")


def load_and_preprocess_log(csv_path: str = LOG_CSV_PATH) -> pd.DataFrame:
    """Loads CSV and applies standard filtering and index conversion."""
    if not os.path.exists(csv_path):
        logging.warning("Log CSV not found at %s", csv_path)
        return pd.DataFrame()

    df = pd.read_csv(csv_path)
    if df.empty:
        return df

    # Filter api_ok
    df["api_ok"] = df["api_ok"].astype(str).str.lower().isin(["true", "1", "yes"])
    df = df[df["api_ok"]].copy()

    if df.empty:
        return df

    # Convert timestamps
    df["dt"] = pd.to_datetime(df["timestamp_ist"])
    df = df.sort_values(by="dt").reset_index(drop=True)

    # Convert ratio to live level and live index
    levels = []
    indices = []
    for r in df["ratio"]:
        lvl, idx = ratio_to_level_and_index(float(r))
        levels.append(lvl)
        indices.append(idx)
    df["live_level"] = levels
    df["live_index"] = indices

    # Compute baseline profile_index
    profile_indices = []
    for _, row in df.iterrows():
        weather = {
            "temp_c": float(row.get("temp_c", 28.0)),
            "rain_mm": float(row.get("rain_mm", 0.0)),
            "clouds_pct": int(row.get("clouds_pct", 20))
        }
        p_idx = predict_profile(row["dt"], weather=weather)
        profile_indices.append(p_idx)
    df["profile_index"] = profile_indices

    return df


def calibrate_region(df_region: pd.DataFrame, region_name: str, total_region_rows: int) -> dict:
    """Performs chronological split, offset computation, and metrics evaluation."""
    n_usable = len(df_region)
    coverage = round(n_usable / total_region_rows, 3) if total_region_rows > 0 else 0.0

    if n_usable < MIN_CALIBRATION_SAMPLES:
        return {
            "region": region_name,
            "offset": 0.0,
            "n_usable": n_usable,
            "n_train": 0,
            "n_test": 0,
            "mae_before": None,
            "mae_after": None,
            "acc_before": None,
            "acc_after": None,
            "coverage": coverage,
            "status": "not enough data"
        }

    # Chronological 70% Train / 30% Test split
    df_sorted = df_region.sort_values(by="dt").reset_index(drop=True)
    n_train = int(np.floor(0.70 * n_usable))
    n_test = n_usable - n_train

    df_train = df_sorted.iloc[:n_train]
    df_test = df_sorted.iloc[n_train:]

    # Offset on Train: mean(live_index - profile_index)
    train_diff = df_train["live_index"] - df_train["profile_index"]
    offset = float(np.round(train_diff.mean(), 4))

    # Test Evaluation
    y_true = df_test["live_index"].values
    y_true_levels = df_test["live_level"].values

    # Before calibration
    y_pred_before = df_test["profile_index"].values
    mae_before = float(np.round(np.mean(np.abs(y_pred_before - y_true)), 4))
    pred_levels_before = [index_to_level(idx) for idx in y_pred_before]
    acc_before = float(np.round(np.mean(np.array(pred_levels_before) == y_true_levels), 4))

    # After calibration (clipped to [0, 1])
    y_pred_after = np.clip(y_pred_before + offset, 0.0, 1.0)
    mae_after = float(np.round(np.mean(np.abs(y_pred_after - y_true)), 4))
    pred_levels_after = [index_to_level(idx) for idx in y_pred_after]
    acc_after = float(np.round(np.mean(np.array(pred_levels_after) == y_true_levels), 4))

    return {
        "region": region_name,
        "offset": offset,
        "n_usable": n_usable,
        "n_train": n_train,
        "n_test": n_test,
        "mae_before": mae_before,
        "mae_after": mae_after,
        "acc_before": acc_before,
        "acc_after": acc_after,
        "coverage": coverage,
        "status": "calibrated"
    }


def run_calibration(csv_path: str = LOG_CSV_PATH) -> dict:
    """Runs calibration across all configured regions and saves artifacts."""
    raw_df = pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()
    processed_df = load_and_preprocess_log(csv_path)

    results = {}
    report_rows = []

    for reg_key in REGIONS.keys():
        total_rows = len(raw_df[raw_df["region"] == reg_key]) if not raw_df.empty else 0
        reg_df = processed_df[processed_df["region"] == reg_key] if not processed_df.empty else pd.DataFrame()

        calib_res = calibrate_region(reg_df, reg_key, total_rows)
        results[reg_key] = calib_res
        report_rows.append(calib_res)

    # Save to JSON
    os.makedirs(os.path.dirname(CALIBRATION_JSON_PATH), exist_ok=True)
    with open(CALIBRATION_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logging.info("Saved calibration JSON to %s", CALIBRATION_JSON_PATH)

    # Save to CSV Report
    os.makedirs(os.path.dirname(CALIBRATION_REPORT_CSV_PATH), exist_ok=True)
    report_df = pd.DataFrame(report_rows)
    report_df.to_csv(CALIBRATION_REPORT_CSV_PATH, index=False)
    logging.info("Saved calibration CSV report to %s", CALIBRATION_REPORT_CSV_PATH)

    return results


if __name__ == "__main__":
    logging.info("Running calibration pipeline...")
    res = run_calibration()
    print(json.dumps(res, indent=2))
