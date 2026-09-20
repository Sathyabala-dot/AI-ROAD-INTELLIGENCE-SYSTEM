"""
services/health_service.py

Loads the trained ML pipeline (preprocessing + RandomForestRegressor)
once at startup and exposes a predict_health_score() function used by
the API and by prediction/predict_health.py.
"""

from __future__ import annotations
import os
import json
import joblib
import pandas as pd
import numpy as np

from health_score_target import classify_condition

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
MODEL_PATH = os.path.join(MODELS_DIR, "road_health_model.pkl")
FEATURE_COLUMNS_PATH = os.path.join(MODELS_DIR, "feature_columns.json")


class HealthModelNotFoundError(Exception):
    pass


class HealthScoreService:
    """Wraps the saved sklearn Pipeline. Loads lazily so importing this
    module (e.g. for tests) doesn't require a trained model to exist."""

    def __init__(self):
        self._pipeline = None
        self._feature_columns = None

    def _ensure_loaded(self):
        if self._pipeline is not None:
            return
        if not os.path.exists(MODEL_PATH):
            raise HealthModelNotFoundError(
                f"Model file not found at {MODEL_PATH}. "
                f"Run `python training/train_health_model.py` first."
            )
        if not os.path.exists(FEATURE_COLUMNS_PATH):
            raise HealthModelNotFoundError(
                f"Feature column contract not found at {FEATURE_COLUMNS_PATH}. "
                f"Re-run training."
            )
        self._pipeline = joblib.load(MODEL_PATH)
        with open(FEATURE_COLUMNS_PATH) as f:
            self._feature_columns = json.load(f)

    def predict(self, observation: dict) -> dict:
        """observation: dict of raw (already feature-engineered) fields
        for a single road observation. Returns health score + condition."""
        self._ensure_loaded()

        numeric_features = self._feature_columns["numeric_features"]
        categorical_features = self._feature_columns["categorical_features"]
        all_features = numeric_features + categorical_features

        row = {col: observation.get(col) for col in all_features}
        X = pd.DataFrame([row])

        raw_pred = self._pipeline.predict(X)[0]
        score = float(np.clip(raw_pred, 0, 100))
        condition = classify_condition(score)

        return {
            "predicted_health_score": round(score, 2),
            "condition": condition,
        }

    def is_ready(self) -> bool:
        return os.path.exists(MODEL_PATH) and os.path.exists(FEATURE_COLUMNS_PATH)


# Module-level singleton used by the API
health_service = HealthScoreService()
