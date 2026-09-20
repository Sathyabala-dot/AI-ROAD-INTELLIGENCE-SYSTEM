"""
prediction/predict_congestion.py

Standalone CLI for the Rule-Based Congestion Estimation.

Usage:
    python prediction/predict_congestion.py
"""
import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.congestion_service import estimate_congestion

SAMPLE = {"vehicle_count": 900, "road_type": "arterial", "lane_count": 4}


def main():
    result = estimate_congestion(**SAMPLE)
    print(json.dumps({**SAMPLE, **result}, indent=2))


if __name__ == "__main__":
    main()
