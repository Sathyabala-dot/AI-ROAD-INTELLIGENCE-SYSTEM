"""
training/train_congestion_model.py

NO ML MODEL IS TRAINED HERE — AND THIS IS INTENTIONAL.

The project brief requires: "If the dataset does NOT contain enough
valid traffic/congestion information and a suitable target, do NOT
fabricate an ML congestion model. Instead implement a transparent
rule-based congestion calculation."

The available dataset (real or the synthetic sample) has no genuine
congestion-level ground truth — only a vehicle_count proxy. Training a
classifier against a target that doesn't exist would mean silently
inventing labels, which this project explicitly avoids.

The actual congestion logic lives in services/congestion_service.py
as `estimate_congestion()` — see that file for the full documented
rule set (Rule-Based Congestion Estimation).

FUTURE ENHANCEMENT: if a genuine congestion dataset (e.g. measured
travel-time index, verified congestion labels) becomes available,
implement training here following the exact same pattern as
train_health_model.py (load -> validate -> clean -> feature-select ->
preprocess -> split -> train -> evaluate -> save).
"""

if __name__ == "__main__":
    print(__doc__)
