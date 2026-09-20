"""
generate_sample_data.py

IMPORTANT — READ BEFORE USING
=============================
No real dataset was available for this project at the time Module 2 was
implemented. This script generates a SYNTHETIC, CLEARLY LABELLED sample
dataset so that:

    1. The Module 2 pipeline (validation -> preprocessing -> feature
       engineering -> training -> prediction -> API) is fully runnable
       end-to-end right now.
    2. When real Module 1 output (or a real dataset) becomes available,
       you swap the CSV in data/raw/ and re-run training. No other code
       changes should be required as long as column names match.

DO NOT present metrics produced from this synthetic data as real-world
model accuracy in your report or viva. Always state clearly:

    "Model trained and evaluated on a project-generated synthetic
    dataset because a real labelled dataset was not available at
    implementation time."

The column schema mirrors the "typical Module 1 output" fields listed in
the project brief (road_id, pothole_count, damage_count, damage_type,
damage_severity, damaged_area_percent, vehicle_count, confidence_score,
GPS coordinates, timestamp), plus commonly-available road/weather/
maintenance attributes so every feature-engineering branch in the
pipeline has something real to operate on.

Run:
    python generate_sample_data.py
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

RNG_SEED = 42
N_ROADS = 60
OBSERVATIONS_PER_ROAD = 8   # simulates repeated observations over time
OUTPUT_PATH = os.path.join("data", "raw", "sample_road_observations.csv")

DAMAGE_TYPES = ["pothole", "crack", "rutting", "raveling", "none"]
ROAD_TYPES = ["highway", "arterial", "collector", "residential"]
WEATHER_CONDITIONS = ["clear", "rain", "overcast", "fog"]


def generate_dataset(seed: int = RNG_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []

    # Tamil Nadu rough bounding box for plausible GPS coordinates
    lat_range = (8.1, 13.5)
    lon_range = (76.8, 80.3)

    road_meta = []
    for i in range(N_ROADS):
        road_meta.append({
            "road_id": f"R{i+1:04d}",
            "road_type": rng.choice(ROAD_TYPES, p=[0.1, 0.25, 0.35, 0.3]),
            "road_length_km": round(float(rng.uniform(0.5, 12.0)), 2),
            "road_age_years": int(rng.integers(1, 30)),
            "lane_count": int(rng.choice([2, 4, 6], p=[0.5, 0.35, 0.15])),
            "latitude": round(float(rng.uniform(*lat_range)), 6),
            "longitude": round(float(rng.uniform(*lon_range)), 6),
            "days_since_maintenance": int(rng.integers(10, 900)),
            "maintenance_count_last_year": int(rng.integers(0, 5)),
        })

    base_time = datetime(2025, 1, 1)
    obs_id = 1
    for meta in road_meta:
        # roads that haven't been maintained in a long time tend to be worse
        degradation_bias = min(meta["days_since_maintenance"] / 900.0, 1.0)

        for k in range(OBSERVATIONS_PER_ROAD):
            timestamp = base_time + timedelta(days=int(rng.integers(0, 400)))

            pothole_count = int(max(0, rng.poisson(2 + 6 * degradation_bias)))
            damage_count = int(max(0, pothole_count + rng.poisson(1 + 3 * degradation_bias)))
            damaged_area_percent = float(np.clip(
                rng.normal(10 + 40 * degradation_bias, 8), 0, 100
            ))
            damage_type = rng.choice(DAMAGE_TYPES, p=[0.3, 0.3, 0.15, 0.15, 0.10])
            damage_severity = int(np.clip(
                round(rng.normal(1 + 3 * degradation_bias, 1)), 0, 5
            ))
            vehicle_count = int(max(0, rng.normal(
                800 if meta["road_type"] in ("highway", "arterial") else 250, 150
            )))
            confidence_score = float(np.clip(rng.normal(0.87, 0.08), 0.4, 0.99))

            rainfall_mm = float(max(0, rng.exponential(4)))
            temperature_c = float(np.clip(rng.normal(29, 4), 15, 42))
            humidity_pct = float(np.clip(rng.normal(70, 12), 20, 100))
            weather_condition = rng.choice(
                WEATHER_CONDITIONS, p=[0.55, 0.2, 0.2, 0.05]
            )

            # historical accident flag: more likely on degraded, high traffic roads
            accident_prob = np.clip(
                0.03 + 0.25 * degradation_bias + (vehicle_count / 4000), 0, 0.9
            )
            historical_accident_count = int(rng.binomial(3, accident_prob))

            rows.append({
                "observation_id": obs_id,
                "road_id": meta["road_id"],
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "road_type": meta["road_type"],
                "road_length_km": meta["road_length_km"],
                "road_age_years": meta["road_age_years"],
                "lane_count": meta["lane_count"],
                "latitude": meta["latitude"],
                "longitude": meta["longitude"],
                "pothole_count": pothole_count,
                "damage_count": damage_count,
                "damage_type": damage_type,
                "damage_severity": damage_severity,
                "damaged_area_percent": round(damaged_area_percent, 2),
                "vehicle_count": vehicle_count,
                "confidence_score": round(confidence_score, 3),
                "rainfall_mm": round(rainfall_mm, 2),
                "temperature_c": round(temperature_c, 1),
                "humidity_pct": round(humidity_pct, 1),
                "weather_condition": weather_condition,
                "days_since_maintenance": meta["days_since_maintenance"],
                "maintenance_count_last_year": meta["maintenance_count_last_year"],
                "historical_accident_count": historical_accident_count,
            })
            obs_id += 1

    df = pd.DataFrame(rows)

    # Inject a small amount of realistic messiness so the preprocessing
    # code has genuine work to do (this dataset does NOT come with a
    # labelled health score column on purpose — see CASE B in feature
    # engineering / training docs).
    dup_idx = rng.choice(df.index, size=5, replace=False)
    df = pd.concat([df, df.loc[dup_idx]], ignore_index=True)  # duplicates

    missing_idx = rng.choice(df.index, size=15, replace=False)
    df.loc[missing_idx, "confidence_score"] = np.nan

    missing_idx2 = rng.choice(df.index, size=8, replace=False)
    df.loc[missing_idx2, "damage_type"] = np.nan

    return df


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df = generate_dataset()
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Synthetic sample dataset written to: {OUTPUT_PATH}")
    print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    print("\nColumn dtypes:")
    print(df.dtypes)
    print("\nNOTE: This is SYNTHETIC data for pipeline demonstration only.")
