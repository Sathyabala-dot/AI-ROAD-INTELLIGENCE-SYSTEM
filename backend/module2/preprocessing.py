"""
preprocessing.py

Reusable scikit-learn preprocessing pipeline. The SAME fitted pipeline
object is saved after training and reloaded at prediction time, so
training-time and inference-time preprocessing can never drift apart.
"""

from __future__ import annotations
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

# These lists define the CONTRACT between feature_engineering.py output
# and this preprocessor. If you add a new engineered feature, add its
# name to the right list here too.
NUMERIC_FEATURES = [
    "pothole_count",
    "damage_count",
    "damaged_area_percent",
    "damage_severity",
    "vehicle_count",
    "confidence_score",
    "road_length_km",
    "road_age_years",
    "lane_count",
    "rainfall_mm",
    "temperature_c",
    "humidity_pct",
    "days_since_maintenance",
    "maintenance_count_last_year",
    "historical_accident_count",
    "damage_density",          # engineered
    "pothole_ratio",           # engineered
]

CATEGORICAL_FEATURES = [
    "road_type",
    "damage_type",
    "weather_condition",
]


def build_preprocessor(numeric_features=None, categorical_features=None) -> ColumnTransformer:
    """Build (but do not fit) the ColumnTransformer.

    Only columns that are actually present in the training dataframe
    should be passed in — see feature_engineering.select_available_features.
    """
    numeric_features = numeric_features if numeric_features is not None else NUMERIC_FEATURES
    categorical_features = categorical_features if categorical_features is not None else CATEGORICAL_FEATURES

    numeric_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    transformers = []
    if numeric_features:
        transformers.append(("num", numeric_pipeline, numeric_features))
    if categorical_features:
        transformers.append(("cat", categorical_pipeline, categorical_features))

    return ColumnTransformer(transformers=transformers, remainder="drop")


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning applied BEFORE the sklearn pipeline: drop exact
    duplicates and rows with a missing road_id (cannot be used)."""
    df = df.drop_duplicates().copy()
    df = df[df["road_id"].notna()].copy()
    return df.reset_index(drop=True)
