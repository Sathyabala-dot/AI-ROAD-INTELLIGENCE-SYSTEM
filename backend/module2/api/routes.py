"""
api/routes.py

All Module 2 API endpoints.

Step 2 improvement:
    Observation -> observation_id -> Prediction

Every /predict/road request:
    1. Validates the observation
    2. Generates the ML/rule-based prediction
    3. Ensures the road exists
    4. Stores the observation
    5. Gets the generated observation_id
    6. Stores the prediction using that observation_id
    7. Keeps the road_id and observation relationship consistent
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

# Allow imports from the module2 root directory
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from api.schemas import (
    RoadObservationRequest,
    HealthPredictionResponse,
    FullPredictionResponse,
    CongestionRequest,
    AccidentRiskRequest,
    HealthCheckResponse,
)

from services.health_service import (
    health_service,
    HealthModelNotFoundError,
)

from services.congestion_service import estimate_congestion
from services.accident_service import estimate_accident_risk
from services.maintenance_service import compute_maintenance_priority

from backend.module2.feature_engineering import engineer_features
from database.connection import get_session, check_connection


router = APIRouter()


# ---------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------
@router.get("/health", response_model=HealthCheckResponse)
def health_check():
    """
    Check API, ML model, and database status.
    """
    return HealthCheckResponse(
        status="ok",
        model_loaded=health_service.is_ready(),
        database_connected=check_connection(),
    )


# ---------------------------------------------------------------------
# Helper: feature engineering for one observation
# ---------------------------------------------------------------------
def _engineer_single(observation: dict) -> dict:
    """
    Convert one observation dictionary into the feature format
    expected by the health prediction service.
    """
    df = pd.DataFrame([observation])
    df = engineer_features(df)

    return df.iloc[0].to_dict()


# ---------------------------------------------------------------------
# Helper: normalize timestamp
# ---------------------------------------------------------------------
def _get_observation_timestamp(timestamp):
    """
    Convert the incoming timestamp into a naive UTC datetime.

    PostgreSQL schema uses TIMESTAMP (without timezone), so an aware
    datetime is converted to UTC and then timezone information is removed.

    If no timestamp is supplied, the current UTC time is used.
    """
    if timestamp is None:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    if timestamp.tzinfo is not None:
        return timestamp.astimezone(timezone.utc).replace(tzinfo=None)

    return timestamp


# ---------------------------------------------------------------------
# POST /predict/health
# ML health score only
# ---------------------------------------------------------------------
@router.post(
    "/predict/health",
    response_model=HealthPredictionResponse,
)
def predict_health(observation: RoadObservationRequest):
    """
    Generate only the ML-based road health prediction.

    This endpoint does not store a database prediction.
    The complete database-linked workflow is handled by /predict/road.
    """

    if not health_service.is_ready():
        raise HTTPException(
            status_code=503,
            detail=(
                "Health model not found. "
                "Run training/train_health_model.py first."
            ),
        )

    try:
        observation_data = observation.model_dump()

        engineered = _engineer_single(observation_data)

        result = health_service.predict(engineered)

    except HealthModelNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Prediction failed: {e}",
        )

    return HealthPredictionResponse(
        road_id=observation.road_id,
        predicted_health_score=result["predicted_health_score"],
        condition=result["condition"],
    )


# ---------------------------------------------------------------------
# POST /predict/road
#
# Full pipeline:
# health + congestion + accident + maintenance
#
# STEP 2 DATABASE FLOW:
#
# Request
#    ↓
# Road
#    ↓
# Observation
#    ↓
# observation_id
#    ↓
# Prediction
# ---------------------------------------------------------------------
@router.post(
    "/predict/road",
    response_model=FullPredictionResponse,
)
def predict_road(observation: RoadObservationRequest):
    """
    Generate a complete road prediction and store it in the database.

    Step 2 guarantees that:
        road_observations.observation_id
                    ↓
        road_health_predictions.observation_id

    The prediction is therefore traceable to the exact observation
    that generated it.
    """

    # -----------------------------------------------------------------
    # 1. Verify ML model
    # -----------------------------------------------------------------
    if not health_service.is_ready():
        raise HTTPException(
            status_code=503,
            detail=(
                "Health model not found. "
                "Run training/train_health_model.py first."
            ),
        )

    # -----------------------------------------------------------------
    # 2. Generate prediction
    # -----------------------------------------------------------------
    try:
        observation_data = observation.model_dump()

        # Engineer ML features
        engineered = _engineer_single(observation_data)

        # Health prediction
        health_result = health_service.predict(engineered)

        # Congestion prediction
        congestion_result = estimate_congestion(
            vehicle_count=observation.vehicle_count,
            road_type=observation.road_type,
            lane_count=observation.lane_count,
        )

        # Accident risk prediction
        accident_result = estimate_accident_risk(
            health_score=health_result["predicted_health_score"],
            damage_severity=observation.damage_severity,
            vehicle_count=observation.vehicle_count,
            weather_condition=observation.weather_condition,
            historical_accident_count=observation.historical_accident_count,
        )

        # Maintenance priority
        maintenance_result = compute_maintenance_priority(
            health_score=health_result["predicted_health_score"],
            accident_risk=accident_result["accident_risk"],
            congestion_level=congestion_result["congestion_level"],
            damage_severity=observation.damage_severity,
        )

    except HealthModelNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Prediction failed: {e}",
        )

    # -----------------------------------------------------------------
    # 3. Build API response
    # -----------------------------------------------------------------
    response = FullPredictionResponse(
        road_id=observation.road_id,
        health_score=health_result["predicted_health_score"],
        condition=health_result["condition"],
        congestion=congestion_result["congestion_level"],
        accident_risk=accident_result["accident_risk"],
        maintenance_priority=maintenance_result["maintenance_priority"],
        latitude=observation.latitude,
        longitude=observation.longitude,
    )

    # -----------------------------------------------------------------
    # 4. Database storage
    # -----------------------------------------------------------------
    #
    # If the database is unavailable, we still return the prediction.
    #
    # If the database IS available, however, the complete transaction
    # must succeed:
    #
    #     Road
    #       ↓
    #     Observation
    #       ↓
    #     Prediction
    #
    # We no longer silently ignore database errors.
    # -----------------------------------------------------------------

    if check_connection():

        try:
            observation_timestamp = _get_observation_timestamp(
                observation.timestamp
            )

            with get_session() as session:

                # =====================================================
                # STEP 2A
                # Ensure the road exists
                # =====================================================
                session.execute(
                    text(
                        """
                        INSERT INTO roads (
                            road_id,
                            road_type,
                            road_length_km,
                            road_age_years,
                            lane_count
                        )
                        VALUES (
                            :road_id,
                            :road_type,
                            :road_length_km,
                            :road_age_years,
                            :lane_count
                        )
                        ON CONFLICT (road_id)
                        DO UPDATE SET
                            road_type = COALESCE(
                                EXCLUDED.road_type,
                                roads.road_type
                            ),
                            road_length_km = COALESCE(
                                EXCLUDED.road_length_km,
                                roads.road_length_km
                            ),
                            road_age_years = COALESCE(
                                EXCLUDED.road_age_years,
                                roads.road_age_years
                            ),
                            lane_count = COALESCE(
                                EXCLUDED.lane_count,
                                roads.lane_count
                            )
                        """
                    ),
                    {
                        "road_id": observation.road_id,
                        "road_type": observation.road_type,
                        "road_length_km": observation.road_length_km,
                        "road_age_years": observation.road_age_years,
                        "lane_count": observation.lane_count,
                    },
                )

                # =====================================================
                # STEP 2B
                # Insert the observation
                #
                # IMPORTANT:
                # PostgreSQL generates observation_id automatically
                # because it is BIGSERIAL PRIMARY KEY.
                # =====================================================
                observation_result = session.execute(
                    text(
                        """
                        INSERT INTO road_observations (
                            road_id,
                            "timestamp",
                            pothole_count,
                            damage_count,
                            damage_type,
                            damage_severity,
                            damaged_area_percent,
                            vehicle_count,
                            confidence_score,
                            rainfall_mm,
                            temperature_c,
                            humidity_pct,
                            weather_condition,
                            days_since_maintenance,
                            maintenance_count_last_year,
                            historical_accident_count,
                            latitude,
                            longitude
                        )
                        VALUES (
                            :road_id,
                            :timestamp,
                            :pothole_count,
                            :damage_count,
                            :damage_type,
                            :damage_severity,
                            :damaged_area_percent,
                            :vehicle_count,
                            :confidence_score,
                            :rainfall_mm,
                            :temperature_c,
                            :humidity_pct,
                            :weather_condition,
                            :days_since_maintenance,
                            :maintenance_count_last_year,
                            :historical_accident_count,
                            :latitude,
                            :longitude
                        )
                        RETURNING observation_id
                        """
                    ),
                    {
                        "road_id": observation.road_id,
                        "timestamp": observation_timestamp,
                        "pothole_count": observation.pothole_count,
                        "damage_count": observation.damage_count,
                        "damage_type": observation.damage_type,
                        "damage_severity": observation.damage_severity,
                        "damaged_area_percent": observation.damaged_area_percent,
                        "vehicle_count": observation.vehicle_count,
                        "confidence_score": observation.confidence_score,
                        "rainfall_mm": observation.rainfall_mm,
                        "temperature_c": observation.temperature_c,
                        "humidity_pct": observation.humidity_pct,
                        "weather_condition": observation.weather_condition,
                        "days_since_maintenance": observation.days_since_maintenance,
                        "maintenance_count_last_year": (
                            observation.maintenance_count_last_year
                        ),
                        "historical_accident_count": (
                            observation.historical_accident_count
                        ),
                        "latitude": observation.latitude,
                        "longitude": observation.longitude,
                    },
                )

                # =====================================================
                # STEP 2C
                # Get generated observation_id
                # =====================================================
                observation_id = observation_result.scalar_one()

                # =====================================================
                # STEP 2D
                # Insert prediction linked to exact observation
                #
                # The road_id is obtained FROM road_observations using
                # observation_id. This prevents the API from accidentally
                # associating the prediction with a different road.
                # =====================================================
                session.execute(
                    text(
                        """
                        INSERT INTO road_health_predictions (
                            road_id,
                            observation_id,
                            health_score,
                            condition,
                            congestion_level,
                            accident_risk,
                            maintenance_priority,
                            latitude,
                            longitude
                        )
                        SELECT
                            road_id,
                            :observation_id,
                            :health_score,
                            :condition,
                            :congestion_level,
                            :accident_risk,
                            :maintenance_priority,
                            :latitude,
                            :longitude
                        FROM road_observations
                        WHERE observation_id = :observation_id
                        """
                    ),
                    {
                        "observation_id": observation_id,
                        "health_score": response.health_score,
                        "condition": response.condition,
                        "congestion_level": response.congestion,
                        "accident_risk": response.accident_risk,
                        "maintenance_priority": (
                            response.maintenance_priority
                        ),
                        "latitude": observation.latitude,
                        "longitude": observation.longitude,
                    },
                )

                # The get_session() context manager is responsible for
                # committing the successful transaction.

        except Exception as e:
            # Do not silently ignore database errors.
            # If DB is reachable but Step 2 storage fails, report it.
            raise HTTPException(
                status_code=500,
                detail=(
                    "Prediction generated, but database storage failed. "
                    f"Reason: {e}"
                ),
            )

    # -----------------------------------------------------------------
    # 5. Return prediction
    # -----------------------------------------------------------------
    return response


# ---------------------------------------------------------------------
# POST /predict/congestion
# Rule-based only
# ---------------------------------------------------------------------
@router.post("/predict/congestion")
def predict_congestion(req: CongestionRequest):
    """
    Estimate congestion using the rule-based congestion service.
    """
    try:
        return estimate_congestion(
            vehicle_count=req.vehicle_count,
            road_type=req.road_type,
            lane_count=req.lane_count,
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Congestion prediction failed: {e}",
        )


# ---------------------------------------------------------------------
# POST /predict/accident-risk
# Rule-based only
# ---------------------------------------------------------------------
@router.post("/predict/accident-risk")
def predict_accident_risk(req: AccidentRiskRequest):
    """
    Estimate accident risk using the rule-based accident service.
    """
    try:
        return estimate_accident_risk(
            health_score=req.health_score,
            damage_severity=req.damage_severity,
            vehicle_count=req.vehicle_count,
            weather_condition=req.weather_condition,
            historical_accident_count=req.historical_accident_count,
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Accident risk prediction failed: {e}",
        )


# ---------------------------------------------------------------------
# GET /roads
# List roads
# ---------------------------------------------------------------------
@router.get("/roads")
def list_roads(limit: int = 100):
    """
    Return roads stored in the database.
    """

    if not check_connection():
        raise HTTPException(
            status_code=503,
            detail="Database not reachable.",
        )

    try:
        with get_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT
                        road_id,
                        road_name,
                        road_type,
                        road_length_km,
                        road_age_years,
                        lane_count
                    FROM roads
                    ORDER BY road_id
                    LIMIT :limit
                    """
                ),
                {"limit": limit},
            ).mappings().all()

        return [dict(row) for row in rows]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}",
        )


# ---------------------------------------------------------------------
# GET /roads/{road_id}
# ---------------------------------------------------------------------
@router.get("/roads/{road_id}")
def get_road(road_id: str):
    """
    Return information for one road.
    """

    if not check_connection():
        raise HTTPException(
            status_code=503,
            detail="Database not reachable.",
        )

    try:
        with get_session() as session:
            row = session.execute(
                text(
                    """
                    SELECT
                        road_id,
                        road_name,
                        road_type,
                        road_length_km,
                        road_age_years,
                        lane_count
                    FROM roads
                    WHERE road_id = :road_id
                    """
                ),
                {"road_id": road_id},
            ).mappings().first()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"Road '{road_id}' not found.",
            )

        return dict(row)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}",
        )


# ---------------------------------------------------------------------
# GET /road-health
# Latest prediction for every road
#
# Includes observation_id so the prediction can be traced back to
# the exact observation that produced it.
# ---------------------------------------------------------------------
@router.get("/road-health")
def list_road_health(limit: int = 200):
    """
    Return the latest prediction for each road.

    observation_id is included for Step 2 traceability.
    """

    if not check_connection():
        raise HTTPException(
            status_code=503,
            detail="Database not reachable.",
        )

    try:
        with get_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT DISTINCT ON (road_id)
                        road_id,
                        observation_id,
                        health_score,
                        condition,
                        congestion_level,
                        accident_risk,
                        maintenance_priority,
                        latitude,
                        longitude,
                        prediction_time,
                        model_version
                    FROM road_health_predictions
                    ORDER BY
                        road_id,
                        prediction_time DESC,
                        prediction_id DESC
                    LIMIT :limit
                    """
                ),
                {"limit": limit},
            ).mappings().all()

        return [dict(row) for row in rows]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}",
        )


# ---------------------------------------------------------------------
# GET /road-health/{road_id}
# Latest prediction for one road
#
# Includes observation_id for Step 2 traceability.
# ---------------------------------------------------------------------
@router.get("/road-health/{road_id}")
def get_road_health(road_id: str):
    """
    Return the latest prediction for one road.

    observation_id identifies the exact observation used to create
    that prediction.
    """

    if not check_connection():
        raise HTTPException(
            status_code=503,
            detail="Database not reachable.",
        )

    try:
        with get_session() as session:
            row = session.execute(
                text(
                    """
                    SELECT
                        road_id,
                        observation_id,
                        health_score,
                        condition,
                        congestion_level,
                        accident_risk,
                        maintenance_priority,
                        latitude,
                        longitude,
                        prediction_time,
                        model_version
                    FROM road_health_predictions
                    WHERE road_id = :road_id
                    ORDER BY
                        prediction_time DESC,
                        prediction_id DESC
                    LIMIT 1
                    """
                ),
                {"road_id": road_id},
            ).mappings().first()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No prediction data found for road "
                    f"'{road_id}'."
                ),
            )

        return dict(row)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}",
        )