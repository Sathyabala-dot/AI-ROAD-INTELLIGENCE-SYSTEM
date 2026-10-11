"""
validation.py

Data validation for road observation data coming from Module 1 (or from
a CSV dataset). This validates structure and value ranges BEFORE any
preprocessing or feature engineering happens.

Used by:
    - training/train_health_model.py (validates the training CSV)
    - api/schemas.py (Pydantic validates individual API requests; this
      module additionally validates bulk/dataframe input)
"""

from __future__ import annotations
import pandas as pd
from dataclasses import dataclass, field


REQUIRED_COLUMNS = [
    "road_id",
    "pothole_count",
    "damage_count",
    "damaged_area_percent",
    "vehicle_count",
    "confidence_score",
]

# Columns that are used if present, but not strictly required
OPTIONAL_COLUMNS = [
    "damage_type",
    "damage_severity",
    "road_type",
    "road_length_km",
    "road_age_years",
    "lane_count",
    "latitude",
    "longitude",
    "rainfall_mm",
    "temperature_c",
    "humidity_pct",
    "weather_condition",
    "days_since_maintenance",
    "maintenance_count_last_year",
    "historical_accident_count",
    "timestamp",
]

RANGE_CHECKS = {
    "pothole_count": (0, 10_000),
    "damage_count": (0, 10_000),
    "damaged_area_percent": (0, 100),
    "vehicle_count": (0, 1_000_000),
    "confidence_score": (0, 1),
    "damage_severity": (0, 5),
    "latitude": (-90, 90),
    "longitude": (-180, 180),
    "humidity_pct": (0, 100),
    "days_since_maintenance": (0, 100_000),
}


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def validate_dataframe(df: pd.DataFrame) -> ValidationResult:
    """Validate a bulk dataframe (e.g. the training CSV)."""
    errors = []
    warnings = []

    if df.empty:
        errors.append("Dataset is empty.")
        return ValidationResult(False, errors, warnings)

    missing_required = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_required:
        errors.append(f"Missing required columns: {missing_required}")

    missing_optional = [c for c in OPTIONAL_COLUMNS if c not in df.columns]
    if missing_optional:
        warnings.append(
            f"Optional columns not present (related features will be skipped): "
            f"{missing_optional}"
        )

    if errors:
        # Can't safely range-check if required columns are missing
        return ValidationResult(False, errors, warnings)

    for col, (lo, hi) in RANGE_CHECKS.items():
        if col in df.columns:
            series = df[col].dropna()
            out_of_range = series[(series < lo) | (series > hi)]
            if not out_of_range.empty:
                warnings.append(
                    f"Column '{col}' has {len(out_of_range)} value(s) outside "
                    f"expected range [{lo}, {hi}]; these will be clipped/handled "
                    f"in preprocessing."
                )

    dup_count = df.duplicated().sum()
    if dup_count > 0:
        warnings.append(f"{dup_count} fully duplicated row(s) found.")

    null_road_id = df["road_id"].isna().sum()
    if null_road_id > 0:
        errors.append(f"{null_road_id} row(s) have a missing road_id.")

    is_valid = len(errors) == 0
    return ValidationResult(is_valid, errors, warnings)


def validate_single_observation(record: dict) -> ValidationResult:
    """Validate a single road observation dict (used as a secondary check
    behind Pydantic validation in the API layer)."""
    errors = []
    warnings = []

    missing_required = [c for c in REQUIRED_COLUMNS if c not in record or record[c] is None]
    if missing_required:
        errors.append(f"Missing required fields: {missing_required}")
        return ValidationResult(False, errors, warnings)

    for col, (lo, hi) in RANGE_CHECKS.items():
        if col in record and record[col] is not None:
            val = record[col]
            if not (lo <= val <= hi):
                errors.append(f"Field '{col}' value {val} out of range [{lo}, {hi}].")

    return ValidationResult(len(errors) == 0, errors, warnings)
