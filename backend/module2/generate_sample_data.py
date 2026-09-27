import os
import numpy as np
import pandas as pd


# Make the generated data reproducible
np.random.seed(42)


# Number of road observations
NUM_SAMPLES = 500


def generate_sample_data():
    data = {
        "road_id": [
            f"RD{i:04d}" for i in range(1, NUM_SAMPLES + 1)
        ],

        "latitude": np.random.uniform(8.0, 13.5, NUM_SAMPLES),

        "longitude": np.random.uniform(76.0, 80.5, NUM_SAMPLES),

        "pothole_count": np.random.randint(0, 21, NUM_SAMPLES),

        "crack_percentage": np.round(
            np.random.uniform(0, 100, NUM_SAMPLES), 2
        ),

        "roughness": np.round(
            np.random.uniform(1, 10, NUM_SAMPLES), 2
        ),

        "traffic_volume": np.random.randint(
            100, 5001, NUM_SAMPLES
        ),

        "drainage_condition": np.round(
            np.random.uniform(0, 100, NUM_SAMPLES), 2
        ),

        "surface_condition": np.round(
            np.random.uniform(0, 100, NUM_SAMPLES), 2
        ),
    }

    df = pd.DataFrame(data)

    # Create a simple development target.
    # Higher road problems reduce the health score.
    score = (
        100
        - (df["pothole_count"] * 2.0)
        - (df["crack_percentage"] * 0.30)
        - (df["roughness"] * 3.0)
        + (df["drainage_condition"] * 0.10)
        + (df["surface_condition"] * 0.10)
    )

    # Keep score within 0-100
    df["health_score"] = np.clip(score, 0, 100)

    # Round the target
    df["health_score"] = df["health_score"].round(2)

    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

    output_path = "data/sample_road_data.csv"

    df.to_csv(output_path, index=False)

    print(f"Sample dataset created: {output_path}")
    print(f"Number of records: {len(df)}")
    print("\nFirst 5 records:")
    print(df.head())


if __name__ == "__main__":
    generate_sample_data()