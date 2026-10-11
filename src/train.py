import json
import logging
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import f1_score, classification_report

from src.config import (
    MUMBAI_THANE_DATA_PATH,
    RAW_DATA_PATH,
    PROCESSED_DATA_PATH,
    MODEL_PATH,
    META_PATH,
    MODELS_DIR,
    DATA_PROCESSED_DIR,
    LEVEL_NAMES
)
from src.features import (
    load_and_preprocess_mumbai_thane,
    MODEL_FEATURE_COLUMNS
)
from src.profile import build_network_profiles

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def train_mumbai_thane_model():
    logging.info("Starting Mumbai-Thane Traffic Model Training Pipeline...")
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    csv_file = MUMBAI_THANE_DATA_PATH if MUMBAI_THANE_DATA_PATH.exists() else RAW_DATA_PATH
    logging.info(f"Loading dataset from {csv_file}...")
    
    df, how_mean_dict = load_and_preprocess_mumbai_thane(csv_file)
    logging.info(f"Loaded {len(df)} records across {df['node_id'].nunique()} nodes.")
    
    # Save processed features
    try:
        df.to_parquet(PROCESSED_DATA_PATH, index=False)
        logging.info(f"Saved processed features to {PROCESSED_DATA_PATH}")
    except Exception as e:
        csv_fallback = DATA_PROCESSED_DIR / "mumbai_thane_features.csv"
        df.to_csv(csv_fallback, index=False)
        logging.info(f"Saved processed features to CSV fallback at {csv_fallback} ({e})")
        
    # Chronological 80/20 train/test split on unique timestamps
    timestamps = df["timestamp"].drop_duplicates().sort_values().values
    split_idx = int(len(timestamps) * 0.8)
    split_time = timestamps[split_idx]
    
    train_df = df[df["timestamp"] < split_time].copy()
    test_df = df[df["timestamp"] >= split_time].copy()
    logging.info(f"Train split: {len(train_df)} rows (< {split_time}), Test split: {len(test_df)} rows (>= {split_time})")
    
    # 1. Baseline: most common congestion level by (node_id, day_of_week, hour) on training set
    baseline_lookup = train_df.groupby(["node_id", "day_of_week", "hour"])["target"].agg(
        lambda s: s.mode().iloc[0] if len(s.mode()) > 0 else 0
    ).to_dict()
    global_mode = int(train_df["target"].mode().iloc[0])
    
    test_baseline_preds = [
        baseline_lookup.get((nid, dow, hr), global_mode)
        for nid, dow, hr in zip(test_df["node_id"], test_df["day_of_week"], test_df["hour"])
    ]
    baseline_f1 = float(f1_score(test_df["target"], test_baseline_preds, average="macro"))
    
    # 2. Train model: HistGradientBoostingClassifier with balanced weights
    logging.info("Training HistGradientBoostingClassifier on 15 features...")
    clf = HistGradientBoostingClassifier(
        random_state=42,
        max_iter=150,
        class_weight="balanced"
    )
    clf.fit(train_df[MODEL_FEATURE_COLUMNS], train_df["target"])
    
    # Evaluate model on held-out test split
    test_model_preds = clf.predict(test_df[MODEL_FEATURE_COLUMNS])
    model_f1 = float(f1_score(test_df["target"], test_model_preds, average="macro"))
    f1_gain_pct = (model_f1 - baseline_f1) * 100.0
    
    logging.info("=" * 65)
    logging.info(f"Baseline Macro-F1 (Hour-of-Week Mode per node): {baseline_f1:.4f}")
    logging.info(f"Model Macro-F1 (HistGradientBoosting):         {model_f1:.4f}")
    logging.info(f"Macro-F1 Gain:                                 +{f1_gain_pct:.2f}%")
    logging.info("=" * 65)
    
    print("\nTest Set Classification Report (Chronological Split):")
    print(classification_report(test_df["target"], test_model_preds, target_names=LEVEL_NAMES, digits=4))
    
    # 3. Permutation Feature Importances on test set sample
    logging.info("Computing permutation feature importances...")
    test_sub = test_df.sample(min(2500, len(test_df)), random_state=42)
    perm = permutation_importance(
        clf,
        test_sub[MODEL_FEATURE_COLUMNS],
        test_sub["target"],
        n_repeats=5,
        random_state=42,
        scoring="f1_macro"
    )
    importances_raw = np.maximum(perm.importances_mean, 0.0)
    imp_sum = np.sum(importances_raw) if np.sum(importances_raw) > 0 else 1.0
    importances_pct = (importances_raw / imp_sum) * 100.0
    
    feature_importances = {
        col: round(float(imp), 2)
        for col, imp in sorted(zip(MODEL_FEATURE_COLUMNS, importances_pct), key=lambda x: x[1], reverse=True)
    }
    logging.info(f"Top 5 Feature Importances: {list(feature_importances.items())[:5]}")
    
    # 4. Build Network & Node-level Profiles
    profiles = build_network_profiles(df)
    
    # 5. Volume Cutoffs
    vols = df["total_vehicle_count"]
    p40, p70, p90 = float(vols.quantile(0.40)), float(vols.quantile(0.70)), float(vols.quantile(0.90))
    cutoffs = {"P40": p40, "P70": p70, "P90": p90}
    
    # 6. Save Model and Metadata Artifacts
    joblib.dump(clf, MODEL_PATH)
    # Also save to generic model.joblib for backward compatibility
    joblib.dump(clf, MODELS_DIR / "model.joblib")
    logging.info(f"Model dumped to {MODEL_PATH}")
    
    meta = {
        "dataset_name": "mumbai_thane_traffic_historical",
        "total_records": len(df),
        "total_nodes": df["node_id"].nunique(),
        "baseline_f1": round(baseline_f1, 4),
        "model_f1": round(model_f1, 4),
        "f1_improvement_pct": round(f1_gain_pct, 2),
        "feature_columns": MODEL_FEATURE_COLUMNS,
        "feature_importances": feature_importances,
        "cutoffs": cutoffs,
        "how_mean_volume": how_mean_dict,
        "global_profile": profiles["global_profile"],
        "node_profiles": profiles["node_profiles"],
        "weekday_curve": profiles["weekday_curve"],
        "weekend_curve": profiles["weekend_curve"],
        # Backward compatibility aliases
        "hourly_profile": profiles["global_profile"],
        "vol_min": float(vols.min()),
        "vol_max": float(vols.max())
    }
    
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)
    with open(MODELS_DIR / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    logging.info(f"Metadata saved to {META_PATH} and models/meta.json")
    
    return meta


if __name__ == "__main__":
    train_mumbai_thane_model()
