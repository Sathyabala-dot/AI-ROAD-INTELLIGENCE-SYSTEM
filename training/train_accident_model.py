"""
training/train_accident_model.py

NO ML MODEL IS TRAINED HERE — AND THIS IS INTENTIONAL.

The available dataset does not contain a sufficiently large or verified
historical-accident dataset to train a reliable classifier (only a
coarse `historical_accident_count` proxy exists in the synthetic
sample). Per the project brief: "If there is no suitable target, do NOT
pretend an ML accident model exists — implement a transparent
rule-based accident-risk score instead."

The actual accident risk logic lives in services/accident_service.py
as `estimate_accident_risk()` — see that file for the full documented
weighted rule set (Rule-Based Accident Risk Estimation).

FUTURE ENHANCEMENT: if a genuine, sufficiently large labelled accident
history dataset becomes available, implement training here following
the exact same pattern as train_health_model.py.
"""

if __name__ == "__main__":
    print(__doc__)
