import torch
import torch.nn as nn
import cv2
import numpy as np
from pathlib import Path

# PATHS

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = PROJECT_ROOT / "models" / "unet" / "unet_pothole.pth"

# Process ALL preprocessed images
IMAGE_DIR = PROJECT_ROOT / "datasets" / "segmentation" / "images"

# Output folders
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "unet_all"
MASK_DIR = OUTPUT_DIR / "masks"
OVERLAY_DIR = OUTPUT_DIR / "overlays"

MASK_DIR.mkdir(parents=True, exist_ok=True)
OVERLAY_DIR.mkdir(parents=True, exist_ok=True)

# U-NET MODEL

class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()

        self.block = nn.Sequential(
            nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size=3,
                padding=1
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),

            nn.Conv2d(
                out_channels,
                out_channels,
                kernel_size=3,
                padding=1
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.block(x)

class UNet(nn.Module):

    def __init__(self):
        super().__init__()

        # Encoder
        self.enc1 = DoubleConv(3, 32)
        self.enc2 = DoubleConv(32, 64)
        self.enc3 = DoubleConv(64, 128)
        self.enc4 = DoubleConv(128, 256)

        self.pool = nn.MaxPool2d(2)

        # Bottleneck
        self.bottleneck = DoubleConv(256, 512)

        # Decoder
        self.up4 = nn.ConvTranspose2d(512, 256, 2, stride=2)
        self.dec4 = DoubleConv(512, 256)

        self.up3 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.dec3 = DoubleConv(256, 128)

        self.up2 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.dec2 = DoubleConv(128, 64)

        self.up1 = nn.ConvTranspose2d(64, 32, 2, stride=2)
        self.dec1 = DoubleConv(64, 32)

        self.output = nn.Conv2d(32, 1, 1)

    def forward(self, x):

        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        e4 = self.enc4(self.pool(e3))

        b = self.bottleneck(self.pool(e4))

        d4 = self.up4(b)
        d4 = torch.cat([d4, e4], dim=1)
        d4 = self.dec4(d4)

        d3 = self.up3(d4)
        d3 = torch.cat([d3, e3], dim=1)
        d3 = self.dec3(d3)

        d2 = self.up2(d3)
        d2 = torch.cat([d2, e2], dim=1)
        d2 = self.dec2(d2)

        d1 = self.up1(d2)
        d1 = torch.cat([d1, e1], dim=1)
        d1 = self.dec1(d1)

        return self.output(d1)

# LOAD MODEL

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("=" * 60)
print("U-NET BATCH INFERENCE")
print("=" * 60)

print(f"Model      : {MODEL_PATH}")
print(f"Image folder: {IMAGE_DIR}")
print(f"Device     : {device}")


model = UNet().to(device)

checkpoint = torch.load(
    MODEL_PATH,
    map_location=device,
    weights_only=False
)

if isinstance(checkpoint, dict):

    if "model_state_dict" in checkpoint:
        state_dict = checkpoint["model_state_dict"]

    elif "state_dict" in checkpoint:
        state_dict = checkpoint["state_dict"]

    else:
        state_dict = checkpoint

else:
    state_dict = checkpoint


model.load_state_dict(state_dict)

model.eval()

print("U-Net model loaded successfully.")

# GET ALL IMAGES

image_extensions = [
    "*.jpg",
    "*.jpeg",
    "*.png",
    "*.JPG",
    "*.JPEG",
    "*.PNG"
]

image_files = []

for extension in image_extensions:
    image_files.extend(IMAGE_DIR.glob(extension))

# Remove duplicates
image_files = sorted(set(image_files))

print()
print(f"Total images found: {len(image_files)}")

if len(image_files) == 0:
    print("ERROR: No images found.")
    print(f"Check folder: {IMAGE_DIR}")
    exit()

# PROCESS ALL IMAGES

total = len(image_files)

successful = 0
failed = 0

area_values = []


for index, image_path in enumerate(image_files, start=1):

    try:

        # Read image

        image = cv2.imread(str(image_path))

        if image is None:
            print(f"[{index}/{total}] FAILED: {image_path.name}")
            failed += 1
            continue

        original_height, original_width = image.shape[:2]

        # Resize for U-Net

        resized = cv2.resize(
            image,
            (256, 256)
        )

        # OpenCV BGR -> RGB
        rgb = cv2.cvtColor(
            resized,
            cv2.COLOR_BGR2RGB
        )

        # Normalize
        rgb = rgb.astype(np.float32) / 255.0

        # HWC -> CHW
        tensor = torch.from_numpy(
            rgb.transpose(2, 0, 1)
        )

        # Add batch dimension
        tensor = tensor.unsqueeze(0).to(device)

        # U-Net prediction

        with torch.no_grad():

            prediction = model(tensor)

            probability = torch.sigmoid(prediction)

            mask = (
                probability[0, 0].cpu().numpy() > 0.55
            ).astype(np.uint8)

        # Resize mask back to original image size

        mask = cv2.resize(
            mask,
            (original_width, original_height),
            interpolation=cv2.INTER_NEAREST
        )

        # Calculate pothole area

        pothole_pixels = int(np.sum(mask))

        total_pixels = mask.shape[0] * mask.shape[1]

        pothole_area = (
            pothole_pixels / total_pixels
        ) * 100

        area_values.append(pothole_area)

        # Save mask

        mask_image = (mask * 255).astype(np.uint8)

        mask_path = (
            MASK_DIR /
            f"{image_path.stem}_mask.png"
        )

        cv2.imwrite(
            str(mask_path),
            mask_image
        )

        # Create overlay

        overlay = image.copy()

        # Create red mask
        red_mask = np.zeros_like(image)

        red_mask[:, :, 2] = 255

        # Blend only pothole pixels
        pothole_region = mask == 1

        overlay[pothole_region] = cv2.addWeighted(
            image[pothole_region],
            0.5,
            red_mask[pothole_region],
            0.5,
            0
        )

        overlay_path = (
            OVERLAY_DIR /
            f"{image_path.stem}_overlay.jpg"
        )

        cv2.imwrite(
            str(overlay_path),
            overlay
        )

        successful += 1

        print(
            f"[{index}/{total}] "
            f"{image_path.name} "
            f"-> Pothole area: {pothole_area:.2f}%"
        )

    except Exception as error:

        failed += 1

        print(
            f"[{index}/{total}] FAILED: "
            f"{image_path.name}"
        )

        print(f"Error: {error}")

# FINAL SUMMARY

print()
print("=" * 60)
print("BATCH INFERENCE COMPLETED")
print("=" * 60)

print(f"Total images : {total}")
print(f"Successful   : {successful}")
print(f"Failed       : {failed}")

if area_values:

    average_area = np.mean(area_values)

    maximum_area = np.max(area_values)

    minimum_area = np.min(area_values)

    print()
    print(f"Average pothole area : {average_area:.2f}%")
    print(f"Minimum pothole area : {minimum_area:.2f}%")
    print(f"Maximum pothole area : {maximum_area:.2f}%")

print()
print("Output folders:")
print(f"Masks    : {MASK_DIR}")
print(f"Overlays : {OVERLAY_DIR}")

print()
print("All images processed successfully.")