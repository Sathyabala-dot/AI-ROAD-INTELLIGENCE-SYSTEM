"""
prediction/predict_accident_risk.py

Standalone CLI for the Rule-Based Accident Risk Estimation. Note that
this requires a health_score input (typically produced by predict_health
first) since health is one of the weighted risk factors.

Usage:
    python prediction/predict_accident_risk.py
"""
import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.accident_service import estimate_accident_risk

SAMPLE = {
    "health_score": 58.4,
    "damage_severity": 3,
    "vehicle_count": 900,
    "weather_condition": "rain",
    "historical_accident_count": 1,
}


def main():
    result = estimate_accident_risk(**SAMPLE)
    print(json.dumps({**SAMPLE, **result}, indent=2))


if __name__ == "__main__":
    main()
