import os
from ultralytics import settings

# Force Ultralytics to use a local datasets directory inside your project folder
current_dir = os.path.dirname(os.path.abspath(__file__))
local_datasets_path = os.path.join(current_dir, "datasets")
os.makedirs(local_datasets_path, exist_ok=True)

# Update Ultralytics global settings to avoid root C:\ permission blocks
settings.update({"datasets_dir": local_datasets_path})

from ultralytics import YOLO

def train_road_model():
    model = YOLO("yolov8s.pt")

    results = model.train(
        data="coco8.yaml",
        epochs=3,
        imgsz=640,
        batch=8,
        project=os.path.join(current_dir, "runs")
    )

    print("Model training complete! Saved weights ready for inference.")

if __name__ == '__main__':
    train_road_model()