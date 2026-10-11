"""
prediction/predict_health.py

Standalone CLI for predicting a road's health score from a JSON file or
inline sample, without needing the API running. Useful for quick testing
and for the viva demo.

Usage:
    python prediction/predict_health.py                       # uses built-in sample
    python prediction/predict_health.py path/to/observation.json
"""

import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.health_service import health_service
from backend.module2.feature_engineering import engineer_features
import pandas as pd

SAMPLE_OBSERVATION = {
    "road_id": "R0001",
    "pothole_count": 12,
    "damage_count": 18,
    "damage_type": "pothole",
    "damage_severity": 3,
    "damaged_area_percent": 35.5,
    "vehicle_count": 900,
    "confidence_score": 0.88,
    "road_type": "arterial",
    "road_length_km": 4.2,
    "road_age_years": 12,
    "lane_count": 4,
    "rainfall_mm": 6.0,
    "temperature_c": 30.5,
    "humidity_pct": 72,
    "weather_condition": "rain",
    "days_since_maintenance": 420,
    "maintenance_count_last_year": 1,
}


def load_observation(path: str | None) -> dict:
    if path is None:
        print("No input file given — using built-in sample observation.")
        return SAMPLE_OBSERVATION
    with open(path) as f:
        return json.load(f)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    observation = load_observation(path)

    # apply the same engineered features used at training time
    df = pd.DataFrame([observation])
    df = engineer_features(df)
    engineered = df.iloc[0].to_dict()

    result = health_service.predict(engineered)
    output = {
        "road_id": observation.get("road_id"),
        **result,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
