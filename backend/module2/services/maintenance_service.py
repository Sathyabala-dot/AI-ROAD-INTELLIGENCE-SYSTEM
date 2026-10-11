"""
services/maintenance_service.py

RULE-BASED Maintenance Priority scoring.

Combines: health score + accident risk + congestion level + damage
severity into a High/Medium/Low priority. This is explicitly a rule
system, not a model — the logic is documented below and should be
quoted directly in the report/viva.

Logic:
    priority_points = 0
    + 3 if health_score < 40   (Poor/Critical)
    + 1 if health_score < 60   (Moderate)
    + 2 if accident_risk == High
    + 1 if accident_risk == Medium
    + 2 if congestion_level in (High, Severe)
    + 1 if congestion_level == Medium
    + 1 if damage_severity >= 4

    priority_points >= 5  -> High
    priority_points >= 2  -> Medium
    else                  -> Low
"""

from __future__ import annotations


def compute_maintenance_priority(
    health_score: float,
    accident_risk: str,
    congestion_level: str,
    damage_severity: float | None = None,
) -> dict:
    points = 0
    reasons = []

    if health_score < 40:
        points += 3
        reasons.append("health score below 40 (Poor/Critical)")
    elif health_score < 60:
        points += 1
        reasons.append("health score below 60 (Moderate)")

    if accident_risk == "High":
        points += 2
        reasons.append("accident risk High")
    elif accident_risk == "Medium":
        points += 1
        reasons.append("accident risk Medium")

    if congestion_level in ("High", "Severe"):
        points += 2
        reasons.append(f"congestion {congestion_level}")
    elif congestion_level == "Medium":
        points += 1
        reasons.append("congestion Medium")

    if (damage_severity or 0) >= 4:
        points += 1
        reasons.append("damage severity >= 4")

    if points >= 5:
        priority = "High"
    elif points >= 2:
        priority = "Medium"
    else:
        priority = "Low"

    return {
        "maintenance_priority": priority,
        "priority_points": points,
        "reasons": reasons,
        "method": "Rule-Based Maintenance Priority Scoring",
    }
