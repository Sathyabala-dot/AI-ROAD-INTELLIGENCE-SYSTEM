import cv2
import shutil
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SEGMENTATION_IMAGE_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "segmentation"
    / "images"
)

SEGMENTATION_MASK_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "segmentation"
    / "masks"
)

DETECTION_IMAGE_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "detection"
    / "images"
)

DETECTION_LABEL_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "detection"
    / "labels"
)


# ============================================================
# CREATE OUTPUT DIRECTORIES
# ============================================================

DETECTION_IMAGE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DETECTION_LABEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SETTINGS
# ============================================================

# YOLO class ID
# 0 = pothole
CLASS_ID = 0

# Minimum connected-component area.
# Very tiny regions are ignored as noise.
MIN_AREA = 20

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}


# ============================================================
# DISPLAY
# ============================================================

print("=" * 70)
print("GENERATING YOLO DETECTION DATASET")
print("=" * 70)

print(f"Source images : {SEGMENTATION_IMAGE_DIR}")
print(f"Source masks  : {SEGMENTATION_MASK_DIR}")
print(f"Output images : {DETECTION_IMAGE_DIR}")
print(f"Output labels : {DETECTION_LABEL_DIR}")
print()


# ============================================================
# CHECK SOURCE DIRECTORIES
# ============================================================

if not SEGMENTATION_IMAGE_DIR.exists():
    raise FileNotFoundError(
        f"Segmentation image folder not found:\n"
        f"{SEGMENTATION_IMAGE_DIR}"
    )

if not SEGMENTATION_MASK_DIR.exists():
    raise FileNotFoundError(
        f"Segmentation mask folder not found:\n"
        f"{SEGMENTATION_MASK_DIR}"
    )


# ============================================================
# FIND IMAGES
# ============================================================

image_files = sorted(
    [
        path
        for path in SEGMENTATION_IMAGE_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
)


print(f"Images found: {len(image_files)}")
print()


if len(image_files) == 0:
    raise RuntimeError(
        "No segmentation images were found."
    )


# ============================================================
# PROCESS IMAGES
# ============================================================

successful = 0
skipped = 0
failed = 0

total_boxes = 0


for index, image_path in enumerate(
    image_files,
    start=1
):

    try:

        # ----------------------------------------------------
        # FIND CORRESPONDING MASK
        # ----------------------------------------------------

        possible_masks = [
            SEGMENTATION_MASK_DIR
            / f"{image_path.stem}_mask.png",

            SEGMENTATION_MASK_DIR
            / f"{image_path.stem}.png",
        ]

        mask_path = None

        for candidate in possible_masks:

            if candidate.exists():
                mask_path = candidate
                break

        if mask_path is None:

            print(
                f"[{index}/{len(image_files)}] "
                f"SKIPPED: mask not found for "
                f"{image_path.name}"
            )

            skipped += 1
            continue


        # ----------------------------------------------------
        # READ IMAGE
        # ----------------------------------------------------

        image = cv2.imread(
            str(image_path)
        )

        if image is None:

            print(
                f"[{index}/{len(image_files)}] "
                f"FAILED: could not read image "
                f"{image_path.name}"
            )

            failed += 1
            continue


        # ----------------------------------------------------
        # READ MASK
        # ----------------------------------------------------

        mask = cv2.imread(
            str(mask_path),
            cv2.IMREAD_GRAYSCALE
        )

        if mask is None:

            print(
                f"[{index}/{len(image_files)}] "
                f"FAILED: could not read mask "
                f"{mask_path.name}"
            )

            failed += 1
            continue


        # ----------------------------------------------------
        # MAKE SURE MASK SIZE MATCHES IMAGE
        # ----------------------------------------------------

        image_height, image_width = image.shape[:2]

        if mask.shape[:2] != (
            image_height,
            image_width
        ):

            mask = cv2.resize(
                mask,
                (
                    image_width,
                    image_height
                ),
                interpolation=cv2.INTER_NEAREST
            )


        # ----------------------------------------------------
        # CONVERT MASK TO BINARY
        # ----------------------------------------------------

        binary_mask = (
            mask > 127
        ).astype("uint8") * 255


        # ----------------------------------------------------
        # FIND CONNECTED POTHOLE REGIONS
        # ----------------------------------------------------

        num_labels, labels, stats, centroids = (
            cv2.connectedComponentsWithStats(
                binary_mask,
                connectivity=8
            )
        )


        yolo_labels = []


        # ----------------------------------------------------
        # PROCESS EACH POTHOLE REGION
        # ----------------------------------------------------

        for component_id in range(
            1,
            num_labels
        ):

            x = stats[
                component_id,
                cv2.CC_STAT_LEFT
            ]

            y = stats[
                component_id,
                cv2.CC_STAT_TOP
            ]

            width = stats[
                component_id,
                cv2.CC_STAT_WIDTH
            ]

            height = stats[
                component_id,
                cv2.CC_STAT_HEIGHT
            ]

            area = stats[
                component_id,
                cv2.CC_STAT_AREA
            ]


            # Ignore tiny noise
            if area < MIN_AREA:
                continue


            # ------------------------------------------------
            # CONVERT TO YOLO FORMAT
            # ------------------------------------------------

            center_x = x + width / 2
            center_y = y + height / 2


            # Normalize to 0-1
            normalized_center_x = (
                center_x / image_width
            )

            normalized_center_y = (
                center_y / image_height
            )

            normalized_width = (
                width / image_width
            )

            normalized_height = (
                height / image_height
            )


            label_line = (
                f"{CLASS_ID} "
                f"{normalized_center_x:.6f} "
                f"{normalized_center_y:.6f} "
                f"{normalized_width:.6f} "
                f"{normalized_height:.6f}"
            )

            yolo_labels.append(
                label_line
            )


        # ----------------------------------------------------
        # COPY IMAGE
        # ----------------------------------------------------

        output_image_path = (
            DETECTION_IMAGE_DIR
            / image_path.name
        )

        shutil.copy2(
            image_path,
            output_image_path
        )


        # ----------------------------------------------------
        # SAVE YOLO LABEL
        # ----------------------------------------------------

        output_label_path = (
            DETECTION_LABEL_DIR
            / f"{image_path.stem}.txt"
        )

        with open(
            output_label_path,
            "w",
            encoding="utf-8"
        ) as label_file:

            if yolo_labels:

                label_file.write(
                    "\n".join(yolo_labels)
                )

                total_boxes += len(
                    yolo_labels
                )


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if yolo_labels:

            print(
                f"[{index}/{len(image_files)}] "
                f"{image_path.name} "
                f"-> {len(yolo_labels)} pothole box(es)"
            )

        else:

            print(
                f"[{index}/{len(image_files)}] "
                f"{image_path.name} "
                f"-> no pothole regions"
            )

        successful += 1


    except Exception as error:

        failed += 1

        print(
            f"[{index}/{len(image_files)}] "
            f"FAILED: {image_path.name}"
        )

        print(
            f"Error: {error}"
        )


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("DETECTION DATASET GENERATION COMPLETED")
print("=" * 70)

print(f"Total source images : {len(image_files)}")
print(f"Successful          : {successful}")
print(f"Skipped             : {skipped}")
print(f"Failed              : {failed}")
print(f"Total pothole boxes : {total_boxes}")

print()
print("Detection dataset:")
print(f"Images : {DETECTION_IMAGE_DIR}")
print(f"Labels : {DETECTION_LABEL_DIR}")

print()
print("Each label uses YOLO format:")
print("class_id center_x center_y width height")

print()
print("Class:")
print("0 = pothole")

print()
print("Next step:")
print("Check the generated labels before training YOLO.")