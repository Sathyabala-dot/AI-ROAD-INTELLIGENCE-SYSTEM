"""
services/accident_service.py

RULE-BASED Accident Risk Estimation.

Why rule-based and not ML: the dataset does not contain a verified
historical accident dataset with enough volume/quality to train a
reliable classifier (the synthetic sample includes only a coarse
`historical_accident_count` proxy). Rather than fabricate an ML accident
model on an unreliable/synthetic target, this module implements a
transparent weighted rule system using factors that plausibly correlate
with accident risk: poor road health, high damage severity, high traffic
volume, adverse weather, and historical accident history where available.

FUTURE ENHANCEMENT: if a genuine, sufficiently large accident-history
dataset becomes available, replace this with a trained classifier
(e.g. logistic regression / gradient boosting) following the same
pattern as train_health_model.py.
"""

from __future__ import annotations


def estimate_accident_risk(
    health_score: float,
    damage_severity: float | None,
    vehicle_count: float,
    weather_condition: str | None = None,
    historical_accident_count: int | None = None,
) -> dict:
    """Rule-Based Accident Risk Estimation.

    Combines normalized risk factors (each 0-1) into a weighted score,
    then maps to Low/Medium/High.
    """
    # Poor health -> higher risk
    health_risk = max(0.0, (100 - health_score) / 100)

    # Damage severity (0-5) normalized
    severity_risk = min((damage_severity or 0) / 5.0, 1.0)

    # Traffic volume risk (saturating around 2000 vehicles/day)
    traffic_risk = min(vehicle_count / 2000.0, 1.0)

    # Weather risk
    weather_risk_map = {"clear": 0.0, "overcast": 0.1, "fog": 0.5, "rain": 0.6}
    weather_risk = weather_risk_map.get((weather_condition or "clear").lower(), 0.2)

    # Historical accidents, if known
    history_risk = min((historical_accident_count or 0) / 3.0, 1.0)

    weights = {
        "health": 0.30,
        "severity": 0.20,
        "traffic": 0.20,
        "weather": 0.15,
        "history": 0.15,
    }

    combined = (
        weights["health"] * health_risk
        + weights["severity"] * severity_risk
        + weights["traffic"] * traffic_risk
        + weights["weather"] * weather_risk
        + weights["history"] * history_risk
    )

    if combined < 0.35:
        level = "Low"
    elif combined < 0.6:
        level = "Medium"
    else:
        level = "High"

    return {
        "accident_risk": level,
        "risk_score": round(float(combined), 3),
        "method": "Rule-Based Accident Risk Estimation",
    }
