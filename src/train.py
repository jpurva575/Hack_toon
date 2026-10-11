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
    RAW_DATA_PATH,
    PROCESSED_DATA_PATH,
    MODEL_PATH,
    META_PATH,
    MODELS_DIR,
    DATA_PROCESSED_DIR,
    LEVEL_NAMES
)
from src.features import (
    clean_raw_data,
    engineer_features,
    compute_volume_cutoffs,
    classify_volume_to_level,
    level_to_class_id,
    FEATURE_COLUMNS
)
from src.profile import build_hourly_profile_and_curves

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def train_pipeline():
    logging.info("Starting Feature 1 training pipeline...")
    
    # Ensure directories exist
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load and clean raw historical traffic dataset
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Raw traffic data not found at {RAW_DATA_PATH}")
        
    logging.info(f"Loading raw data from {RAW_DATA_PATH}...")
    df_raw = clean_raw_data(RAW_DATA_PATH)
    logging.info(f"Loaded {len(df_raw)} records after timestamp deduplication.")
    
    # 2. Engineer features
    logging.info("Engineering features and calculating hour-of-week lag proxies...")
    df_feat, how_mean_volume = engineer_features(df_raw)
    
    # 3. Define volume cut points: Low < P40, Moderate P40-P70, High P70-P90, Severe > P90
    cutoffs = compute_volume_cutoffs(df_feat["traffic_volume"])
    logging.info(f"Volume Cutoffs: P40={cutoffs['P40']:.1f}, P70={cutoffs['P70']:.1f}, P90={cutoffs['P90']:.1f}")
    
    # Target label: 0=Low, 1=Moderate, 2=High, 3=Severe
    df_feat["level"] = df_feat["traffic_volume"].apply(lambda v: classify_volume_to_level(v, cutoffs))
    df_feat["target"] = df_feat["level"].apply(level_to_class_id)
    
    # Save processed features
    try:
        df_feat.to_parquet(PROCESSED_DATA_PATH, index=False)
        logging.info(f"Saved processed features to {PROCESSED_DATA_PATH}")
    except Exception as e:
        csv_fallback = DATA_PROCESSED_DIR / "features.csv"
        df_feat.to_csv(csv_fallback, index=False)
        logging.info(f"Saved processed features to CSV fallback at {csv_fallback} ({e})")
        
    # 4. Time-based 80/20 train/test split
    n = len(df_feat)
    split_idx = int(n * 0.8)
    train_df = df_feat.iloc[:split_idx].copy()
    test_df = df_feat.iloc[split_idx:].copy()
    logging.info(f"Train split: {len(train_df)} rows, Test split (held-out last 20%): {len(test_df)} rows")
    
    # 5. Baseline: most common level for each hour-of-week on train set
    baseline_lookup = train_df.groupby(["day_of_week", "hour"])["target"].agg(
        lambda s: s.mode().iloc[0] if len(s.mode()) > 0 else 0
    ).to_dict()
    
    test_baseline_preds = test_df.apply(
        lambda r: baseline_lookup.get((r["day_of_week"], r["hour"]), 0),
        axis=1
    )
    baseline_f1 = float(f1_score(test_df["target"], test_baseline_preds, average="macro"))
    
    # 6. Train model
    logging.info("Training HistGradientBoostingClassifier...")
    clf = HistGradientBoostingClassifier(
        max_iter=150,
        random_state=42,
        class_weight="balanced"
    )
    clf.fit(train_df[FEATURE_COLUMNS], train_df["target"])
    
    # Evaluate model
    test_model_preds = clf.predict(test_df[FEATURE_COLUMNS])
    model_f1 = float(f1_score(test_df["target"], test_model_preds, average="macro"))
    
    logging.info("=" * 60)
    logging.info(f"Baseline Macro-F1 (Hour-of-Week Mode): {baseline_f1:.4f}")
    logging.info(f"Model Macro-F1:                         {model_f1:.4f}")
    logging.info(f"Macro-F1 Gain:                          {(model_f1 - baseline_f1)*100:+.2f}%")
    logging.info("=" * 60)
    
    # Classification Report
    print("\nTest Set Classification Report:")
    print(classification_report(test_df["target"], test_model_preds, target_names=LEVEL_NAMES, digits=4))
    
    # 7. Compute Feature Importances (Permutation Importance on test subset)
    logging.info("Computing feature importances via permutation...")
    test_sub = test_df.sample(min(2000, len(test_df)), random_state=42)
    perm = permutation_importance(
        clf,
        test_sub[FEATURE_COLUMNS],
        test_sub["target"],
        n_repeats=5,
        random_state=42,
        scoring="f1_macro"
    )
    importances_raw = np.maximum(perm.importances_mean, 0.0)
    importances_sum = np.sum(importances_raw) if np.sum(importances_raw) > 0 else 1.0
    importances_pct = (importances_raw / importances_sum) * 100.0
    
    feature_importances = {
        col: round(float(imp), 2)
        for col, imp in sorted(zip(FEATURE_COLUMNS, importances_pct), key=lambda x: x[1], reverse=True)
    }
    logging.info(f"Feature Importances: {feature_importances}")
    
    # 8. Compute Hourly Profile and Curves
    profile_data = build_hourly_profile_and_curves(df_feat, cutoffs)
    
    # 9. Save artifacts: model.joblib and meta.json
    joblib.dump(clf, MODEL_PATH)
    logging.info(f"Saved trained model to {MODEL_PATH}")
    
    meta = {
        "cutoffs": cutoffs,
        "baseline_f1": round(baseline_f1, 4),
        "model_f1": round(model_f1, 4),
        "f1_improvement_pct": round((model_f1 - baseline_f1) * 100, 2),
        "feature_columns": FEATURE_COLUMNS,
        "feature_importances": feature_importances,
        "how_mean_volume": how_mean_volume,
        "hourly_profile": profile_data["hourly_profile"],
        "weekday_curve": profile_data["weekday_curve"],
        "weekend_curve": profile_data["weekend_curve"],
        "vol_min": profile_data["vol_min"],
        "vol_max": profile_data["vol_max"]
    }
    
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)
    logging.info(f"Saved metadata and profiles to {META_PATH}")
    
    return meta


if __name__ == "__main__":
    train_pipeline()
