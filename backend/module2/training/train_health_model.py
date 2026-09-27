import os

import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from preprocessing.preprocess import load_data, prepare_data


DATA_PATH = "data/sample_road_data.csv"
MODEL_PATH = "models/health_score_model.pkl"


def train_model():

    # Load and prepare data
    df = load_data(DATA_PATH)

    X, y = prepare_data(df)

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    print(f"\nTraining records: {len(X_train)}")
    print(f"Testing records: {len(X_test)}")

    # Create the ML model
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )

    # Train the model
    print("\nTraining model...")

    model.fit(X_train, y_train)

    print("Model training completed.")

    # Make predictions on test data
    predictions = model.predict(X_test)

    # Calculate evaluation metrics
    mae = mean_absolute_error(y_test, predictions)
    rmse = mean_squared_error(
        y_test,
        predictions
    ) ** 0.5
    r2 = r2_score(y_test, predictions)

    print("\nModel Evaluation")
    print("----------------")
    print(f"MAE  : {mae:.2f}")
    print(f"RMSE : {rmse:.2f}")
    print(f"R²   : {r2:.2f}")

    # Create models directory
    os.makedirs("models", exist_ok=True)

    # Save trained model
    joblib.dump(model, MODEL_PATH)

    print(f"\nModel saved to: {MODEL_PATH}")


if __name__ == "__main__":
    train_model()