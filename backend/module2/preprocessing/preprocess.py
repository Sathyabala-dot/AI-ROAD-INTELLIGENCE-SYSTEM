import pandas as pd


FEATURE_COLUMNS = [
    "pothole_count",
    "crack_percentage",
    "roughness",
    "traffic_volume",
    "drainage_condition",
    "surface_condition"
]

TARGET_COLUMN = "health_score"


def load_data(file_path):
    """Load road data from CSV."""
    df = pd.read_csv(file_path)

    print(f"Loaded {len(df)} records.")

    return df


def validate_data(df):
    """Check whether required columns are available."""

    required_columns = FEATURE_COLUMNS + [TARGET_COLUMN]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    print("Data validation successful.")

    return True


def prepare_data(df):
    """Prepare features and target for model training."""

    validate_data(df)

    # Select model input features
    X = df[FEATURE_COLUMNS].copy()

    # Select target
    y = df[TARGET_COLUMN].copy()

    # Handle missing values
    X = X.fillna(X.median())
    y = y.fillna(y.median())

    print(f"Features: {FEATURE_COLUMNS}")
    print(f"Target: {TARGET_COLUMN}")

    return X, y


if __name__ == "__main__":
    data = load_data("data/sample_road_data.csv")

    X, y = prepare_data(data)

    print("\nFeature data:")
    print(X.head())

    print("\nTarget data:")
    print(y.head())