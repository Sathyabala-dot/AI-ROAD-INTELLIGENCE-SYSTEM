"""
api/schemas.py

Pydantic request/response models. These validate: required fields,
numeric ranges, GPS values, and reject malformed input with proper
HTTP 422 errors automatically (FastAPI + Pydantic default behavior).
"""

from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class RoadObservationRequest(BaseModel):
    """Input coming from Module 1 (or manual/API test input)."""

    road_id: str = Field(..., min_length=1, max_length=20)
    pothole_count: int = Field(..., ge=0, le=10000)
    damage_count: int = Field(..., ge=0, le=10000)
    damage_type: Optional[str] = None
    damage_severity: Optional[int] = Field(default=0, ge=0, le=5)
    damaged_area_percent: float = Field(..., ge=0, le=100)
    vehicle_count: int = Field(..., ge=0, le=1_000_000)
    confidence_score: float = Field(..., ge=0, le=1)

    road_type: Optional[str] = None
    road_length_km: Optional[float] = Field(default=None, ge=0)
    road_age_years: Optional[int] = Field(default=None, ge=0)
    lane_count: Optional[int] = Field(default=None, ge=1, le=20)

    rainfall_mm: Optional[float] = Field(default=0, ge=0)
    temperature_c: Optional[float] = Field(default=None)
    humidity_pct: Optional[float] = Field(default=None, ge=0, le=100)
    weather_condition: Optional[str] = None

    days_since_maintenance: Optional[int] = Field(default=None, ge=0)
    maintenance_count_last_year: Optional[int] = Field(default=None, ge=0)
    historical_accident_count: Optional[int] = Field(default=0, ge=0)

    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    timestamp: Optional[datetime] = None

    @field_validator("road_id")
    @classmethod
    def road_id_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("road_id must not be blank")
        return v.strip()


class HealthPredictionResponse(BaseModel):
    road_id: str
    predicted_health_score: float
    condition: str


class FullPredictionResponse(BaseModel):
    road_id: str
    health_score: float
    condition: str
    congestion: str
    accident_risk: str
    maintenance_priority: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CongestionRequest(BaseModel):
    vehicle_count: int = Field(..., ge=0)
    road_type: Optional[str] = None
    lane_count: Optional[int] = Field(default=2, ge=1, le=20)


class AccidentRiskRequest(BaseModel):
    health_score: float = Field(..., ge=0, le=100)
    damage_severity: Optional[int] = Field(default=0, ge=0, le=5)
    vehicle_count: int = Field(..., ge=0)
    weather_condition: Optional[str] = None
    historical_accident_count: Optional[int] = Field(default=0, ge=0)


class RoadResponse(BaseModel):
    road_id: str
    road_name: Optional[str] = None
    road_type: Optional[str] = None
    road_length_km: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class HealthCheckResponse(BaseModel):
    status: str
    model_loaded: bool
    database_connected: bool
