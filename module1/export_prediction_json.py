
from pathlib import Path
from datetime import datetime
import json

from ultralytics import YOLO

# Existing project paths
ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "models" / "yolo" / "yolo_pothole_best.pt"
IMAGE_DIR = ROOT / "datasets" / "detection" / "images"
OUTPUT_PATH = ROOT / "outputs" / "yolo" / "observation.json"

# Load the trained model
model = YOLO(str(MODEL_PATH))

# Select one road image
extensions = {".jpg", ".jpeg", ".png"}
images = sorted(
    p for p in IMAGE_DIR.iterdir()
    if p.suffix.lower() in extensions
)

if not images:
    raise FileNotFoundError(f"No images found in {IMAGE_DIR}")

image_path = images[0]

# Run actual model inference
result = model.predict(
    source=str(image_path),
    conf=0.25,
    verbose=False
)[0]

boxes = result.boxes
count = len(boxes)


detections = []

for box in boxes:
    x1, y1, x2, y2 = box.xyxy[0].tolist()

    detections.append({
        "damage_type": "pothole",
        "confidence": round(float(box.conf[0]), 4),
        "bounding_box": {
            "x1": round(x1, 2),
            "y1": round(y1, 2),
            "x2": round(x2, 2),
            "y2": round(y2, 2)
        }
    })


confidences = boxes.conf.tolist() if count else []
average_confidence = (
    sum(confidences) / count if count else None
)

# One JSON object per road observation
observation = {
    "observation_id": "OBS_001",
    "road_id": None,
    "timestamp": datetime.now().astimezone().isoformat(),
    "road_type": None,
    "road_length_km": None,
    "road_age_years": None,
    "lane_count": None,
    "latitude": None,
    "longitude": None,
    "pothole_count": count,
    "detections": detections,
    "damage_count": count,
    "damage_type": "pothole" if count else None,
    "damage_severity": "unknown",
    "damaged_area_percent": None,
    "vehicle_count": None,
    "confidence_score": (
        round(average_confidence, 4)
        if average_confidence is not None else None
    ),
    "rainfall_mm": None,
    "temperature_c": None,
    "humidity_pct": None,
    "weather_condition": None,
    "days_since_maintenance": None,
    "maintenance_count_last_year": None,
    "historical_accident_count": None
}

# Save the JSON file
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.write_text(
    json.dumps(observation, indent=2),
    encoding="utf-8"
)

print("Input image:", image_path.name)
print("Pothole detections:", count)
print("Individual confidence scores:", confidences)
print("JSON saved to:", OUTPUT_PATH)
print(json.dumps(observation, indent=2))
