"""
training/train_health_model.py

Complete training pipeline for the Road Health Score regression model.

Steps (per project spec):
  1. Load dataset
  2. Validate dataset
  3. Clean data
  4. Select features
  5. Select target
  6. Perform preprocessing
  7. Split data
  8. Train model
  9. Evaluate model
  10. Save model
  11. Save preprocessing pipeline
  12. Generate evaluation output

Run:
    python training/train_health_model.py

Output:
    models/road_health_model.pkl
    models/preprocessor.pkl
    models/feature_columns.json
    models/evaluation_report.json
"""

import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from backend.module2.validation import validate_dataframe
from backend.module2.preprocessing import build_preprocessor, clean_dataframe
from backend.module2.feature_engineering import engineer_features, select_available_features
from backend.module2.health_score_target import compute_health_score

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "sample_road_observations.csv")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")


def load_dataset(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset not found at {path}.\n"
            f"Run `python generate_sample_data.py` first to create the "
            f"synthetic sample dataset, or place your real dataset at this path."
        )
    return pd.read_csv(path)


def main():
    print("=" * 70)
    print("MODULE 2 — Road Health Score Model Training")
    print("=" * 70)

    # 1. Load dataset
    print("\n[1/12] Loading dataset...")
    df = load_dataset(DATA_PATH)
    print(f"    Loaded {len(df)} rows, {len(df.columns)} columns")

    # 2. Validate dataset
    print("\n[2/12] Validating dataset...")
    result = validate_dataframe(df)
    for w in result.warnings:
        print(f"    WARNING: {w}")
    if not result.is_valid:
        for e in result.errors:
            print(f"    ERROR: {e}")
        raise ValueError("Dataset failed validation. See errors above.")
    print("    Validation passed.")

    # 3. Clean data
    print("\n[3/12] Cleaning data...")
    before = len(df)
    df = clean_dataframe(df)
    print(f"    Removed {before - len(df)} duplicate/invalid rows -> {len(df)} rows remain")

    # 3b. Feature engineering (added columns must exist before selecting features)
    df = engineer_features(df)

    # 4. Select target
    #
    # CASE A (if your real dataset has a genuine labelled health score
    # column, e.g. "road_health_score"): replace the block below with:
    #     y = df["road_health_score"]
    #
    # CASE B (current — no labelled target in the dataset):
    print("\n[4/12] Selecting target (Road Health Score)...")
    if "road_health_score" in df.columns:
        print("    Using existing 'road_health_score' column from dataset (CASE A).")
        y = df["road_health_score"].clip(0, 100)
    else:
        print("    No labelled health score column found — using project-derived")
        print("    target from health_score_target.py (CASE B). See that file for")
        print("    full documented methodology.")
        y = compute_health_score(df)

    # 5. Select features
    print("\n[5/12] Selecting features...")
    numeric_features, categorical_features = select_available_features(df)
    print(f"    Numeric features used ({len(numeric_features)}): {numeric_features}")
    print(f"    Categorical features used ({len(categorical_features)}): {categorical_features}")

    X = df[numeric_features + categorical_features]

    # 6. Build preprocessing pipeline (fit happens inside the full Pipeline below)
    print("\n[6/12] Building preprocessing pipeline...")
    preprocessor = build_preprocessor(numeric_features, categorical_features)

    # 7. Split data
    #
    # The same road_id appears multiple times (repeated observations).
    # A naive random split could leak the same road into both train and
    # test sets. We use GroupShuffleSplit grouped by road_id to avoid this.
    print("\n[7/12] Splitting data (grouped by road_id to avoid leakage)...")
    groups = df["road_id"]
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y, groups=groups))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    print(f"    Train: {len(X_train)} rows | Test: {len(X_test)} rows")
    print(f"    Unique roads in train: {groups.iloc[train_idx].nunique()}, "
          f"test: {groups.iloc[test_idx].nunique()}")

    # 8. Train model
    #
    # Model choice: RandomForestRegressor.
    # Why: tabular data with a mix of numeric + categorical (one-hot)
    # features, moderate dataset size, need for explainability
    # (feature_importances_) for the viva, robust to outliers/scaling
    # issues, no GPU or extra heavy dependency required (unlike
    # XGBoost/LightGBM), and trains fast enough to iterate on a laptop.
    print("\n[8/12] Training model (RandomForestRegressor)...")
    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )

    full_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("model", model),
    ])
    full_pipeline.fit(X_train, y_train)
    print("    Training complete.")

    # 9. Evaluate model
    print("\n[9/12] Evaluating model...")
    y_pred = full_pipeline.predict(X_test)
    y_pred = np.clip(y_pred, 0, 100)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print(f"    MAE  = {mae:.4f}")
    print(f"    RMSE = {rmse:.4f}")
    print(f"    R2   = {r2:.4f}")
    print("\n    NOTE: These metrics are computed from an actual run on the")
    print("    dataset present at data/raw/. If that dataset is the synthetic")
    print("    sample, these numbers reflect synthetic-data performance only")
    print("    and MUST be labelled as such in your report.")

    # 10 & 11. Save model + preprocessing pipeline
    # (saved together as one fitted sklearn Pipeline — this guarantees
    # training-time and inference-time preprocessing never diverge)
    print("\n[10-11/12] Saving model + preprocessing pipeline...")
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "road_health_model.pkl")
    joblib.dump(full_pipeline, model_path)
    print(f"    Saved combined pipeline to {model_path}")

    feature_columns_path = os.path.join(MODELS_DIR, "feature_columns.json")
    with open(feature_columns_path, "w") as f:
        json.dump({
            "numeric_features": numeric_features,
            "categorical_features": categorical_features,
        }, f, indent=2)
    print(f"    Saved feature column contract to {feature_columns_path}")

    # 12. Generate evaluation output
    print("\n[12/12] Writing evaluation report...")
    feature_names = full_pipeline.named_steps["preprocessor"].get_feature_names_out()
    importances = full_pipeline.named_steps["model"].feature_importances_
    importance_pairs = sorted(
        zip(feature_names, importances), key=lambda x: x[1], reverse=True
    )

    report = {
        "trained_on": DATA_PATH,
        "is_synthetic_data": "sample_road_observations.csv" in DATA_PATH,
        "n_train_rows": len(X_train),
        "n_test_rows": len(X_test),
        "target_source": "dataset_column" if "road_health_score" in df.columns else "derived_formula (health_score_target.py)",
        "metrics": {"MAE": round(mae, 4), "RMSE": round(rmse, 4), "R2": round(r2, 4)},
        "top_10_feature_importances": [
            {"feature": str(f), "importance": round(float(i), 4)}
            for f, i in importance_pairs[:10]
        ],
    }
    report_path = os.path.join(MODELS_DIR, "evaluation_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"    Saved evaluation report to {report_path}")

    print("\n" + "=" * 70)
    print("Training complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
