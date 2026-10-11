"""
services/congestion_service.py

RULE-BASED Congestion Estimation.

Why rule-based and not ML: the available dataset (real or synthetic
sample) does not contain a genuine congestion-level target (e.g. actual
travel-time-index or verified congestion labels) — only a vehicle_count
proxy and road capacity attributes (road_type, lane_count). Training an
ML classifier on a target that doesn't exist would mean silently
fabricating a model, which the project brief explicitly forbids.

This module is therefore a transparent, documented scoring function.
If a genuine congestion dataset becomes available later, this can be
replaced with a trained classifier following the same pattern as
train_health_model.py (see FUTURE ENHANCEMENT note in README).
"""

from __future__ import annotations

# Rough per-lane capacity assumptions (vehicles/day) used only to build a
# transparent congestion ratio. These are illustrative project assumptions,
# not measured/calibrated traffic-engineering constants — documented here
# for the report and viva.
LANE_CAPACITY_PER_DAY = {
    "highway": 15000,
    "arterial": 9000,
    "collector": 5000,
    "residential": 2000,
}
DEFAULT_CAPACITY_PER_LANE = 4000


def estimate_congestion(vehicle_count: float, road_type: str | None, lane_count: int | None) -> dict:
    """Rule-Based Congestion Estimation.

    Returns a dict with the congestion level label and the underlying
    ratio, so the API/report can show the reasoning, not just a label.
    """
    lane_count = lane_count or 2
    per_lane_capacity = LANE_CAPACITY_PER_DAY.get(
        (road_type or "").lower(), DEFAULT_CAPACITY_PER_LANE
    )
    total_capacity = per_lane_capacity * lane_count
    total_capacity = max(total_capacity, 1)  # avoid divide-by-zero

    ratio = vehicle_count / total_capacity

    if ratio < 0.4:
        level = "Low"
    elif ratio < 0.75:
        level = "Medium"
    elif ratio < 1.1:
        level = "High"
    else:
        level = "Severe"

    return {
        "congestion_level": level,
        "volume_capacity_ratio": round(float(ratio), 3),
        "method": "Rule-Based Congestion Estimation",
    }
