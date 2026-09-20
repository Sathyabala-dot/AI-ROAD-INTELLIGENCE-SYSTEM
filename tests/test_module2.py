"""
tests/test_module2.py

Covers the 10 required test cases:
 1. Valid health prediction
 2. Invalid input
 3. Missing feature
 4. Negative/invalid road-condition value
 5. Multiple road predictions
 6. Database insertion
 7. Database retrieval
 8. GIS road retrieval
 9. Health API (GET /health)
 10. Model evaluation

Run:
    pytest -v
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import pytest
from fastapi.testclient import TestClient

from api.main import app
from services.health_service import health_service

client = TestClient(app)

VALID_OBSERVATION = {
    "road_id": "R0001",
    "pothole_count": 10,
    "damage_count": 15,
    "damage_type": "pothole",
    "damage_severity": 3,
    "damaged_area_percent": 30.0,
    "vehicle_count": 800,
    "confidence_score": 0.9,
    "road_type": "arterial",
    "road_length_km": 3.5,
    "road_age_years": 10,
    "lane_count": 4,
    "rainfall_mm": 5.0,
    "temperature_c": 29.0,
    "humidity_pct": 68,
    "weather_condition": "clear",
    "days_since_maintenance": 300,
    "maintenance_count_last_year": 1,
    "historical_accident_count": 0,
    "latitude": 13.05,
    "longitude": 80.25,
}

MODEL_AVAILABLE = health_service.is_ready()

skip_if_no_model = pytest.mark.skipif(
    not MODEL_AVAILABLE,
    reason="Model not trained yet — run training/train_health_model.py first.",
)


# ---------------------------------------------------------------------
# Test 9: Health API
# ---------------------------------------------------------------------
def test_09_health_api():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert "model_loaded" in body
    assert "database_connected" in body


# ---------------------------------------------------------------------
# Test 1: Valid health prediction
# ---------------------------------------------------------------------
@skip_if_no_model
def test_01_valid_health_prediction():
    resp = client.post("/predict/health", json=VALID_OBSERVATION)
    assert resp.status_code == 200
    body = resp.json()
    assert body["road_id"] == "R0001"
    assert 0 <= body["predicted_health_score"] <= 100
    assert body["condition"] in ("Excellent", "Good", "Moderate", "Poor", "Critical")


# ---------------------------------------------------------------------
# Test 2: Invalid input (bad type / out-of-range value)
# ---------------------------------------------------------------------
def test_02_invalid_input_out_of_range():
    bad = dict(VALID_OBSERVATION)
    bad["confidence_score"] = 5.0  # out of [0,1] range
    resp = client.post("/predict/health", json=bad)
    assert resp.status_code == 422  # Pydantic validation error


def test_02b_invalid_input_wrong_type():
    bad = dict(VALID_OBSERVATION)
    bad["pothole_count"] = "not-a-number"
    resp = client.post("/predict/health", json=bad)
    assert resp.status_code == 422


# ---------------------------------------------------------------------
# Test 3: Missing required feature
# ---------------------------------------------------------------------
def test_03_missing_required_field():
    incomplete = dict(VALID_OBSERVATION)
    del incomplete["damaged_area_percent"]
    resp = client.post("/predict/health", json=incomplete)
    assert resp.status_code == 422


# ---------------------------------------------------------------------
# Test 4: Negative/invalid road-condition value
# ---------------------------------------------------------------------
def test_04_negative_value_rejected():
    bad = dict(VALID_OBSERVATION)
    bad["pothole_count"] = -5
    resp = client.post("/predict/health", json=bad)
    assert resp.status_code == 422


# ---------------------------------------------------------------------
# Test 5: Multiple road predictions (batch of individual calls)
# ---------------------------------------------------------------------
@skip_if_no_model
def test_05_multiple_road_predictions():
    road_ids = ["R0001", "R0002", "R0003"]
    results = []
    for rid in road_ids:
        obs = dict(VALID_OBSERVATION)
        obs["road_id"] = rid
        resp = client.post("/predict/health", json=obs)
        assert resp.status_code == 200
        results.append(resp.json())
    assert len(results) == 3
    assert {r["road_id"] for r in results} == set(road_ids)


# ---------------------------------------------------------------------
# Test 6 & 7: Database insertion + retrieval (via /predict/road + /road-health)
# These are SKIPPED automatically if no DB is configured/reachable —
# they are not fabricated as passing without a real database.
# ---------------------------------------------------------------------
@pytest.mark.skipif(
    client.get("/health").json().get("database_connected") is not True,
    reason="Database not reachable — configure PostgreSQL/PostGIS and .env to run this test.",
)
@skip_if_no_model
def test_06_and_07_database_insert_and_retrieve():
    resp = client.post("/predict/road", json=VALID_OBSERVATION)
    assert resp.status_code == 200

    resp2 = client.get(f"/road-health/{VALID_OBSERVATION['road_id']}")
    assert resp2.status_code == 200
    body = resp2.json()
    assert body["road_id"] == VALID_OBSERVATION["road_id"]


# ---------------------------------------------------------------------
# Test 8: GIS road retrieval
# ---------------------------------------------------------------------
@pytest.mark.skipif(
    client.get("/health").json().get("database_connected") is not True,
    reason="Database not reachable — configure PostgreSQL/PostGIS and .env to run this test.",
)
def test_08_gis_road_retrieval():
    resp = client.get("/roads?limit=10")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------
# Test 10: Model evaluation report exists and has real (non-fabricated) metrics
# ---------------------------------------------------------------------
@skip_if_no_model
def test_10_model_evaluation_report_exists():
    report_path = os.path.join(
        os.path.dirname(__file__), "..", "models", "evaluation_report.json"
    )
    assert os.path.exists(report_path), (
        "Run training/train_health_model.py to generate the evaluation report."
    )
    with open(report_path) as f:
        report = json.load(f)
    assert "metrics" in report
    assert "MAE" in report["metrics"]
    assert "RMSE" in report["metrics"]
    assert "R2" in report["metrics"]
