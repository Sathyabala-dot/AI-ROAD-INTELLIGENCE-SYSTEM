from pathlib import Path
import random
import shutil

import torch
from ultralytics import YOLO


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# The datasets folder is at the outer project level
DATASET_ROOT = PROJECT_ROOT / "datasets" / "detection"

SOURCE_IMAGES = DATASET_ROOT / "images"
SOURCE_LABELS = DATASET_ROOT / "labels"

TRAIN_IMAGES = DATASET_ROOT / "train" / "images"
TRAIN_LABELS = DATASET_ROOT / "train" / "labels"

VAL_IMAGES = DATASET_ROOT / "val" / "images"
VAL_LABELS = DATASET_ROOT / "val" / "labels"

DATA_YAML = DATASET_ROOT / "data.yaml"

MODEL_DIR = PROJECT_ROOT / "models" / "yolo"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "yolo"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# TRAINING SETTINGS
# ============================================================

MODEL_NAME = "yolov8n.pt"

EPOCHS = 50
IMAGE_SIZE = 640
BATCH_SIZE = 8

VAL_SPLIT = 0.20
SEED = 42

RUN_NAME = "road_pothole_yolo"

DEVICE = 0 if torch.cuda.is_available() else "cpu"


# ============================================================
# DISPLAY INFORMATION
# ============================================================

print("=" * 70)
print("YOLO POTHOLE DETECTION TRAINING")
print("=" * 70)

print(f"Project root : {PROJECT_ROOT}")
print(f"Dataset      : {DATASET_ROOT}")
print(f"Model        : {MODEL_NAME}")
print(f"Epochs       : {EPOCHS}")
print(f"Image size   : {IMAGE_SIZE}")
print(f"Batch size   : {BATCH_SIZE}")
print(f"Device       : {DEVICE}")

print("=" * 70)


# ============================================================
# CHECK SOURCE DATASET
# ============================================================

if not SOURCE_IMAGES.exists():
    raise FileNotFoundError(
        f"\nSource image folder not found:\n{SOURCE_IMAGES}"
    )

if not SOURCE_LABELS.exists():
    raise FileNotFoundError(
        f"\nSource label folder not found:\n{SOURCE_LABELS}"
    )


# ============================================================
# FIND IMAGES
# ============================================================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}


images = sorted(
    [
        p for p in SOURCE_IMAGES.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]
)


if len(images) == 0:
    raise RuntimeError(
        "\nNo images found in:\n"
        f"{SOURCE_IMAGES}"
    )


# ============================================================
# VERIFY IMAGE/LABEL PAIRS
# ============================================================

valid_pairs = []
missing_labels = []

for image_path in images:

    label_path = SOURCE_LABELS / f"{image_path.stem}.txt"

    if label_path.exists():
        valid_pairs.append((image_path, label_path))
    else:
        missing_labels.append(image_path.name)


print()
print("SOURCE DATASET")
print("-" * 70)

print(f"Images found       : {len(images)}")
print(f"Valid image-labels : {len(valid_pairs)}")
print(f"Missing labels     : {len(missing_labels)}")


if missing_labels:

    print()
    print("WARNING: Some images do not have labels.")

    for name in missing_labels[:10]:
        print(f"  {name}")

    if len(missing_labels) > 10:
        print(
            f"  ... and {len(missing_labels) - 10} more"
        )


if len(valid_pairs) == 0:
    raise RuntimeError(
        "\nNo valid image-label pairs found."
    )


# ============================================================
# CREATE TRAIN / VALIDATION SPLIT
# ============================================================

print()
print("=" * 70)
print("CREATING TRAIN / VALIDATION SPLIT")
print("=" * 70)


random.seed(SEED)

random.shuffle(valid_pairs)

split_index = int(
    len(valid_pairs) * (1 - VAL_SPLIT)
)

train_pairs = valid_pairs[:split_index]
val_pairs = valid_pairs[split_index:]


print(f"Total pairs       : {len(valid_pairs)}")
print(f"Training pairs    : {len(train_pairs)}")
print(f"Validation pairs  : {len(val_pairs)}")


# ============================================================
# CLEAR OLD GENERATED SPLIT
# ============================================================

for folder in [
    TRAIN_IMAGES,
    TRAIN_LABELS,
    VAL_IMAGES,
    VAL_LABELS
]:

    if folder.exists():
        shutil.rmtree(folder)

    folder.mkdir(parents=True, exist_ok=True)


# ============================================================
# COPY TRAINING DATA
# ============================================================

print()
print("Copying training data...")

for image_path, label_path in train_pairs:

    shutil.copy2(
        image_path,
        TRAIN_IMAGES / image_path.name
    )

    shutil.copy2(
        label_path,
        TRAIN_LABELS / label_path.name
    )


# ============================================================
# COPY VALIDATION DATA
# ============================================================

print("Copying validation data...")

for image_path, label_path in val_pairs:

    shutil.copy2(
        image_path,
        VAL_IMAGES / image_path.name
    )

    shutil.copy2(
        label_path,
        VAL_LABELS / label_path.name
    )


print("Train/validation split created successfully.")


# ============================================================
# CREATE DATA.YAML
# ============================================================

print()
print("=" * 70)
print("CREATING YOLO DATASET YAML")
print("=" * 70)


yaml_text = f"""path: {DATASET_ROOT.as_posix()}

train: train/images
val: val/images

names:
  0: pothole
"""


DATA_YAML.write_text(
    yaml_text,
    encoding="utf-8"
)


print(f"Data YAML created:")
print(DATA_YAML)


# ============================================================
# LOAD YOLO DETECTION MODEL
# ============================================================

print()
print("=" * 70)
print("LOADING YOLO DETECTION MODEL")
print("=" * 70)

model = YOLO(MODEL_NAME)

print("YOLO detection model loaded successfully.")


# ============================================================
# TRAIN
# ============================================================

print()
print("=" * 70)
print("STARTING YOLO TRAINING")
print("=" * 70)

results = model.train(

    data=str(DATA_YAML),

    epochs=EPOCHS,

    imgsz=IMAGE_SIZE,

    batch=BATCH_SIZE,

    device=DEVICE,

    project=str(OUTPUT_DIR),

    name=RUN_NAME,

    pretrained=True,

    patience=10,

    save=True,

    plots=True,

    workers=0,

    verbose=True
)


# ============================================================
# TRAINING COMPLETED
# ============================================================

print()
print("=" * 70)
print("YOLO TRAINING COMPLETED")
print("=" * 70)


RUN_DIR = OUTPUT_DIR / RUN_NAME

BEST_MODEL = (
    RUN_DIR
    / "weights"
    / "best.pt"
)

LAST_MODEL = (
    RUN_DIR
    / "weights"
    / "last.pt"
)


print(f"Training output : {RUN_DIR}")


# ============================================================
# CHECK MODEL FILES
# ============================================================

print()
print("MODEL FILES")
print("-" * 70)


if BEST_MODEL.exists():

    print(f"Best model : {BEST_MODEL}")

else:

    print("WARNING: best.pt was not found.")


if LAST_MODEL.exists():

    print(f"Last model : {LAST_MODEL}")

else:

    print("WARNING: last.pt was not found.")


# ============================================================
# COPY BEST MODEL
# ============================================================

if BEST_MODEL.exists():

    FINAL_MODEL = (
        MODEL_DIR
        / "yolo_pothole_best.pt"
    )

    shutil.copy2(
        BEST_MODEL,
        FINAL_MODEL
    )

    print()
    print("Best model copied to:")
    print(FINAL_MODEL)


# ============================================================
# VALIDATION
# ============================================================

if BEST_MODEL.exists():

    print()
    print("=" * 70)
    print("VALIDATING BEST YOLO MODEL")
    print("=" * 70)

    best_model = YOLO(
        str(BEST_MODEL)
    )

    metrics = best_model.val(

        data=str(DATA_YAML),

        imgsz=IMAGE_SIZE,

        batch=BATCH_SIZE,

        device=DEVICE
    )

    print()
    print("=" * 70)
    print("VALIDATION COMPLETED")
    print("=" * 70)

else:

    print()
    print("Validation skipped because best.pt was not found.")


# ============================================================
# FINAL MESSAGE
# ============================================================

print()
print("=" * 70)
print("YOLO PIPELINE FINISHED")
print("=" * 70)

print()
print("Your trained model should be located at:")

print(
    MODEL_DIR / "yolo_pothole_best.pt"
)

print()
print("Next step:")
print("Use the trained YOLO model for pothole detection.")