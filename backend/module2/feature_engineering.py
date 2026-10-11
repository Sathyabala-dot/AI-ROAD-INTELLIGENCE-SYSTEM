"""
feature_engineering.py

Builds the feature vector from ACTUAL available columns. Distinguishes
AVAILABLE FEATURES (used) from OPTIONAL/FUTURE FEATURES (skipped if the
column isn't present in the given dataframe — never fabricated).
"""

from __future__ import annotations
import pandas as pd
from backend.module2.preprocessing import NUMERIC_FEATURES, CATEGORICAL_FEATURES

# --- AVAILABLE FEATURES (from the synthetic sample / typical Module 1 output) ---
# Visual:       pothole_count, damage_count, damage_type, damage_severity,
#               damaged_area_percent, vehicle_count, confidence_score
# Road:         road_type, road_length_km, road_age_years, lane_count
# Traffic:      vehicle_count (proxy — no dedicated congestion sensor feed)
# Weather:      rainfall_mm, temperature_c, humidity_pct, weather_condition
# Maintenance:  days_since_maintenance, maintenance_count_last_year
#
# --- OPTIONAL / FUTURE FEATURES (not in current dataset — do not fabricate) ---
# - Live CCTV-derived continuous condition stream
# - Crowdsourced pothole reports
# - IoT vibration/accelerometer sensor data
# - Real-time congestion sensor feed (only historical vehicle_count proxy used)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features on top of the raw available columns."""
    df = df.copy()

    if "damage_count" in df.columns and "road_length_km" in df.columns:
        # damage instances per km — normalizes for road length
        df["damage_density"] = df["damage_count"] / df["road_length_km"].replace(0, 0.1)
    else:
        df["damage_density"] = df.get("damage_count", 0)

    if "pothole_count" in df.columns and "damage_count" in df.columns:
        denom = df["damage_count"].replace(0, 1)
        df["pothole_ratio"] = (df["pothole_count"] / denom).clip(0, 1)
    else:
        df["pothole_ratio"] = 0.0

    return df


def select_available_features(df: pd.DataFrame):
    """Return the (numeric_features, categorical_features) lists filtered
    down to columns that actually exist in `df`. This is what keeps the
    pipeline honest when optional columns are missing."""
    numeric = [c for c in NUMERIC_FEATURES if c in df.columns]
    categorical = [c for c in CATEGORICAL_FEATURES if c in df.columns]
    return numeric, categorical
