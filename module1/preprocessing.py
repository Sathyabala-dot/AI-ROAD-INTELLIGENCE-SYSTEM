import cv2
import numpy as np
from pathlib import Path
import shutil

# PATH CONFIGURATION

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_DATASET = (
    PROJECT_ROOT
    / "AI-ROAD-INTELLIGENCE-SYSTEM"
    / "datasets"
    / "pothole_yolo"
    / "Pothole_Segmentation_YOLOv8"
)

OUTPUT_DATASET = PROJECT_ROOT / "datasets" / "segmentation"

OUTPUT_IMAGES = OUTPUT_DATASET / "images"
OUTPUT_MASKS = OUTPUT_DATASET / "masks"


# Supported image formats
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# CREATE DIRECTORIES

def create_directories():
    OUTPUT_IMAGES.mkdir(parents=True, exist_ok=True)
    OUTPUT_MASKS.mkdir(parents=True, exist_ok=True)

    print("Output directories ready:")
    print(f"Images : {OUTPUT_IMAGES}")
    print(f"Masks  : {OUTPUT_MASKS}")

# READ YOLO POLYGON LABEL

def create_mask_from_yolo(label_file, image_width, image_height):
    """
    Convert YOLO polygon segmentation labels into
    a binary OpenCV mask.

    YOLO polygon format:

    class_id x1 y1 x2 y2 x3 y3 ...

    Coordinates are normalized between 0 and 1.
    """

    mask = np.zeros(
        (image_height, image_width),
        dtype=np.uint8
    )

    if not label_file.exists():
        return mask

    with open(label_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    for line_number, line in enumerate(lines, start=1):

        line = line.strip()

        if not line:
            continue

        values = line.split()

        # At least:
        # class_id + 3 coordinate pairs
        if len(values) < 7:
            print(
                f"WARNING: Invalid polygon in "
                f"{label_file.name}, line {line_number}"
            )
            continue

        try:
            class_id = int(float(values[0]))

            coordinates = list(map(float, values[1:]))

        except ValueError:
            print(
                f"WARNING: Non-numeric label in "
                f"{label_file.name}, line {line_number}"
            )
            continue

        # Polygon requires x,y pairs
        if len(coordinates) % 2 != 0:
            print(
                f"WARNING: Odd number of coordinates in "
                f"{label_file.name}, line {line_number}"
            )
            continue

        points = []

        for i in range(0, len(coordinates), 2):

            x_normalized = coordinates[i]
            y_normalized = coordinates[i + 1]

            # Convert normalized coordinates
            # to image pixel coordinates
            x_pixel = int(
                x_normalized * image_width
            )

            y_pixel = int(
                y_normalized * image_height
            )

            # Keep points inside image
            x_pixel = max(
                0,
                min(image_width - 1, x_pixel)
            )

            y_pixel = max(
                0,
                min(image_height - 1, y_pixel)
            )

            points.append(
                [x_pixel, y_pixel]
            )

        if len(points) >= 3:

            polygon = np.array(
                points,
                dtype=np.int32
            )

            # Fill polygon with white
            cv2.fillPoly(
                mask,
                [polygon],
                255
            )

    return mask

# PROCESS ONE DATASET SPLIT

def process_split(split_name):

    images_directory = (
        SOURCE_DATASET
        / split_name
        / "images"
    )

    labels_directory = (
        SOURCE_DATASET
        / split_name
        / "labels"
    )

    if not images_directory.exists():
        print(
            f"\nERROR: Image directory not found:"
            f"\n{images_directory}"
        )
        return 0

    if not labels_directory.exists():
        print(
            f"\nERROR: Label directory not found:"
            f"\n{labels_directory}"
        )
        return 0

    image_files = sorted(
        [
            file
            for file in images_directory.iterdir()
            if file.suffix.lower() in IMAGE_EXTENSIONS
        ]
    )

    print("\n" + "=" * 60)
    print(f"PROCESSING: {split_name.upper()}")
    print("=" * 60)

    print(f"Images found: {len(image_files)}")

    processed_count = 0
    failed_count = 0
    empty_mask_count = 0

    for index, image_file in enumerate(
        image_files,
        start=1
    ):

        print(
            f"[{index}/{len(image_files)}] "
            f"{image_file.name}"
        )

        # Read image

        image = cv2.imread(
            str(image_file)
        )

        if image is None:
            print(
                f"  ERROR: Could not read image"
            )
            failed_count += 1
            continue

        image_height, image_width = image.shape[:2]

        # Find matching label

        label_file = (
            labels_directory
            / f"{image_file.stem}.txt"
        )

        # Create mask

        mask = create_mask_from_yolo(
            label_file,
            image_width,
            image_height
        )

        # Save image

        output_image = (
            OUTPUT_IMAGES
            / image_file.name
        )

        # Avoid filename conflicts between train/valid
        # if necessary.
        if output_image.exists():

            output_image = (
                OUTPUT_IMAGES
                / f"{split_name}_{image_file.name}"
            )

        shutil.copy2(
            image_file,
            output_image
        )

        # Save mask

        output_mask = (
            OUTPUT_MASKS
            / f"{output_image.stem}.png"
        )

        success = cv2.imwrite(
            str(output_mask),
            mask
        )

        if not success:
            print(
                "  ERROR: Could not save mask"
            )
            failed_count += 1
            continue

        # Check mask

        unique_values = np.unique(mask)

        if np.array_equal(
            unique_values,
            np.array([0])
        ):
            empty_mask_count += 1

        processed_count += 1

    print("\nSplit completed:")
    print(f"  Processed      : {processed_count}")
    print(f"  Failed         : {failed_count}")
    print(f"  Empty masks    : {empty_mask_count}")

    return processed_count

# VALIDATE GENERATED DATASET

def validate_output():

    print("\n" + "=" * 60)
    print("VALIDATING GENERATED SEGMENTATION DATASET")
    print("=" * 60)

    image_files = sorted(
        [
            file
            for file in OUTPUT_IMAGES.iterdir()
            if file.suffix.lower()
            in IMAGE_EXTENSIONS
        ]
    )

    mask_files = sorted(
        OUTPUT_MASKS.glob("*.png")
    )

    print(f"Total images : {len(image_files)}")
    print(f"Total masks  : {len(mask_files)}")

    if len(image_files) != len(mask_files):

        print(
            "\nWARNING:"
            "\nImage and mask counts do not match."
        )

    matched = 0
    missing_masks = 0

    for image_file in image_files:

        expected_mask = (
            OUTPUT_MASKS
            / f"{image_file.stem}.png"
        )

        if expected_mask.exists():
            matched += 1
        else:
            missing_masks += 1
            print(
                f"Missing mask: {image_file.name}"
            )

    print(f"\nMatched pairs : {matched}")
    print(f"Missing masks : {missing_masks}")

    # Check a few masks
    print("\nChecking generated masks...")

    checked = 0

    for mask_file in mask_files[:10]:

        mask = cv2.imread(
            str(mask_file),
            cv2.IMREAD_GRAYSCALE
        )

        if mask is None:
            print(
                f"ERROR reading mask: "
                f"{mask_file.name}"
            )
            continue

        unique_values = np.unique(mask)

        print(
            f"{mask_file.name}: "
            f"{unique_values.tolist()}"
        )

        checked += 1

    print(
        f"\nChecked {checked} sample masks."
    )

# MAIN

def main():

    print("=" * 60)
    print("AI ROAD INTELLIGENCE SYSTEM")
    print("MODULE 1 - OPENCV PREPROCESSING")
    print("=" * 60)

    print("\nProject root:")
    print(PROJECT_ROOT)

    print("\nSource dataset:")
    print(SOURCE_DATASET)

    if not SOURCE_DATASET.exists():

        print(
            "\nERROR:"
            "\nSource dataset was not found."
        )

        print(
            "\nExpected location:"
        )

        print(SOURCE_DATASET)

        return

    create_directories()

    # Process training data
    train_count = process_split("train")

    # Process validation data
    valid_count = process_split("valid")

    # Validate final output
    validate_output()

    print("\n" + "=" * 60)
    print("PREPROCESSING COMPLETE")
    print("=" * 60)

    print(
        f"\nTraining images processed : {train_count}"
    )

    print(
        f"Validation images processed : {valid_count}"
    )

    print(
        "\nGenerated dataset:"
    )

    print(
        f"  {OUTPUT_DATASET}"
    )

    print("\nNext stage:")
    print("  U-Net training")


if __name__ == "__main__":
    main()