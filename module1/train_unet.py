import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import cv2
import numpy as np
from pathlib import Path
import random

# PATHS

PROJECT_ROOT = Path(__file__).resolve().parent.parent

IMAGE_DIR = PROJECT_ROOT / "datasets" / "segmentation" / "images"
MASK_DIR = PROJECT_ROOT / "datasets" / "segmentation" / "masks"

MODEL_DIR = PROJECT_ROOT / "models" / "unet"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "unet_pothole.pth"
THRESHOLD_PATH = MODEL_DIR / "unet_threshold.txt"

# SETTINGS

IMAGE_SIZE = 256

BATCH_SIZE = 4

EPOCHS = 40

LEARNING_RATE = 0.0005

VAL_SPLIT = 0.20

SEED = 42

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

# RANDOM SEED

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

# U-NET

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

        self.up4 = nn.ConvTranspose2d(
            512,
            256,
            2,
            stride=2
        )

        self.dec4 = DoubleConv(512, 256)

        self.up3 = nn.ConvTranspose2d(
            256,
            128,
            2,
            stride=2
        )

        self.dec3 = DoubleConv(256, 128)

        self.up2 = nn.ConvTranspose2d(
            128,
            64,
            2,
            stride=2
        )

        self.dec2 = DoubleConv(128, 64)

        self.up1 = nn.ConvTranspose2d(
            64,
            32,
            2,
            stride=2
        )

        self.dec1 = DoubleConv(64, 32)

        self.output = nn.Conv2d(
            32,
            1,
            1
        )

    def forward(self, x):

        e1 = self.enc1(x)

        e2 = self.enc2(
            self.pool(e1)
        )

        e3 = self.enc3(
            self.pool(e2)
        )

        e4 = self.enc4(
            self.pool(e3)
        )

        b = self.bottleneck(
            self.pool(e4)
        )

        d4 = self.up4(b)

        d4 = torch.cat(
            [d4, e4],
            dim=1
        )

        d4 = self.dec4(d4)

        d3 = self.up3(d4)

        d3 = torch.cat(
            [d3, e3],
            dim=1
        )

        d3 = self.dec3(d3)

        d2 = self.up2(d3)

        d2 = torch.cat(
            [d2, e2],
            dim=1
        )

        d2 = self.dec2(d2)

        d1 = self.up1(d2)

        d1 = torch.cat(
            [d1, e1],
            dim=1
        )

        d1 = self.dec1(d1)

        return self.output(d1)


# DATASET

class PotholeDataset(Dataset):

    def __init__(
        self,
        image_files,
        training=False
    ):

        self.image_files = image_files

        self.training = training

    def __len__(self):

        return len(self.image_files)

    def find_mask(self, image_path):

        candidates = [

            MASK_DIR / f"{image_path.stem}_mask.png",

            MASK_DIR / f"{image_path.stem}.png",

            MASK_DIR / f"{image_path.stem}.jpg",

            MASK_DIR / f"{image_path.stem}.jpeg"

        ]

        for path in candidates:

            if path.exists():

                return path

        return None

    def __getitem__(self, index):

        image_path = self.image_files[index]

        mask_path = self.find_mask(image_path)

        if mask_path is None:

            raise FileNotFoundError(
                f"Mask not found for {image_path.name}"
            )

        image = cv2.imread(
            str(image_path)
        )

        mask = cv2.imread(
            str(mask_path),
            cv2.IMREAD_GRAYSCALE
        )

        if image is None:

            raise ValueError(
                f"Could not read image: {image_path}"
            )

        if mask is None:

            raise ValueError(
                f"Could not read mask: {mask_path}"
            )

        # Resize

        image = cv2.resize(
            image,
            (IMAGE_SIZE, IMAGE_SIZE)
        )

        mask = cv2.resize(
            mask,
            (IMAGE_SIZE, IMAGE_SIZE),
            interpolation=cv2.INTER_NEAREST
        )

        # Convert BGR -> RGB

        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        # DATA AUGMENTATION

        if self.training:

            # Horizontal flip
            if random.random() < 0.5:

                image = np.fliplr(
                    image
                ).copy()

                mask = np.fliplr(
                    mask
                ).copy()

            # Vertical flip
            if random.random() < 0.15:

                image = np.flipud(
                    image
                ).copy()

                mask = np.flipud(
                    mask
                ).copy()

            # Small rotation
            if random.random() < 0.30:

                angle = random.uniform(
                    -10,
                    10
                )

                matrix = cv2.getRotationMatrix2D(
                    (
                        IMAGE_SIZE // 2,
                        IMAGE_SIZE // 2
                    ),
                    angle,
                    1.0
                )

                image = cv2.warpAffine(
                    image,
                    matrix,
                    (
                        IMAGE_SIZE,
                        IMAGE_SIZE
                    ),
                    flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REFLECT
                )

                mask = cv2.warpAffine(
                    mask,
                    matrix,
                    (
                        IMAGE_SIZE,
                        IMAGE_SIZE
                    ),
                    flags=cv2.INTER_NEAREST,
                    borderMode=cv2.BORDER_CONSTANT,
                    borderValue=0
                )

            # Mild brightness/contrast
            if random.random() < 0.30:

                alpha = random.uniform(
                    0.85,
                    1.15
                )

                beta = random.uniform(
                    -15,
                    15
                )

                image = cv2.convertScaleAbs(
                    image,
                    alpha=alpha,
                    beta=beta
                )

        # Normalize image

        image = (
            image.astype(
                np.float32
            ) / 255.0
        )

        # Normalize mask

        mask = (
            mask > 127
        ).astype(
            np.float32
        )

        # HWC -> CHW

        image = torch.from_numpy(
            image.transpose(2, 0, 1)
        ).float()

        mask = torch.from_numpy(
            mask
        ).unsqueeze(0).float()

        return image, mask


# DICE LOSS

def dice_loss(
    prediction,
    target,
    smooth=1.0
):

    prediction = torch.sigmoid(
        prediction
    )

    prediction = prediction.contiguous().view(
        -1
    )

    target = target.contiguous().view(
        -1
    )

    intersection = (
        prediction * target
    ).sum()

    dice = (
        2.0 * intersection + smooth
    ) / (
        prediction.sum()
        + target.sum()
        + smooth
    )

    return 1.0 - dice


# DICE SCORE

def dice_score(
    prediction,
    target,
    threshold=0.5
):

    prediction = torch.sigmoid(
        prediction
    )

    prediction = (
        prediction > threshold
    ).float()

    intersection = (
        prediction * target
    ).sum()

    denominator = (
        prediction.sum()
        + target.sum()
    )

    if denominator == 0:

        return 1.0

    dice = (
        2.0 * intersection
    ) / denominator

    return dice.item()


# FIND IMAGES

image_files = sorted(
    list(IMAGE_DIR.glob("*.jpg"))
    + list(IMAGE_DIR.glob("*.jpeg"))
    + list(IMAGE_DIR.glob("*.png"))
)

print("=" * 70)
print("IMPROVED U-NET TRAINING")
print("=" * 70)

print(f"Images found : {len(image_files)}")

print(f"Image folder : {IMAGE_DIR}")

print(f"Mask folder  : {MASK_DIR}")

print(f"Device       : {DEVICE}")

print(f"Epochs       : {EPOCHS}")

print(f"Batch size   : {BATCH_SIZE}")

print(f"Learning rate: {LEARNING_RATE}")


# VERIFY IMAGE/MASK PAIRS

dataset_temp = PotholeDataset(
    image_files,
    training=False
)

valid_images = []

for image_path in image_files:

    if dataset_temp.find_mask(
        image_path
    ) is not None:

        valid_images.append(
            image_path
        )

print(
    f"Valid image/mask pairs: {len(valid_images)}"
)

if len(valid_images) == 0:

    print()
    print("ERROR: No valid image/mask pairs found.")

    print(
        "Check datasets/segmentation/images and masks."
    )

    raise SystemExit


# TRAIN / VALIDATION SPLIT

random.shuffle(
    valid_images
)

split_index = int(
    len(valid_images)
    * (1 - VAL_SPLIT)
)

train_files = valid_images[
    :split_index
]

val_files = valid_images[
    split_index:
]


print(
    f"Training samples  : {len(train_files)}"
)

print(
    f"Validation samples: {len(val_files)}"
)

# DATA LOADERS

train_dataset = PotholeDataset(
    train_files,
    training=True
)

val_dataset = PotholeDataset(
    val_files,
    training=False
)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)

# MODEL

model = UNet().to(
    DEVICE
)

print()
print("U-Net model created.")

# LOSS

bce_loss = nn.BCEWithLogitsLoss()

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=1e-4
)

scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="max",
    factor=0.5,
    patience=4,
    min_lr=1e-6
)

# TRAINING

best_dice = -1.0

best_epoch = 0

patience_counter = 0

EARLY_STOPPING_PATIENCE = 10


for epoch in range(
    1,
    EPOCHS + 1
):

    # TRAIN

    model.train()

    train_loss_total = 0.0

    train_count = 0

    for images, masks in train_loader:

        images = images.to(
            DEVICE
        )

        masks = masks.to(
            DEVICE
        )

        optimizer.zero_grad()

        outputs = model(
            images
        )

        loss_bce = bce_loss(
            outputs,
            masks
        )

        loss_dice = dice_loss(
            outputs,
            masks
        )

        # Balanced combination

        loss = (
            0.5 * loss_bce
            + 0.5 * loss_dice
        )

        loss.backward()

        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            max_norm=1.0
        )

        optimizer.step()

        train_loss_total += (
            loss.item()
            * images.size(0)
        )

        train_count += images.size(0)

    train_loss = (
        train_loss_total
        / train_count
    )

    # VALIDATION

    model.eval()

    val_loss_total = 0.0

    val_count = 0

    dice_total = 0.0

    with torch.no_grad():

        for images, masks in val_loader:

            images = images.to(
                DEVICE
            )

            masks = masks.to(
                DEVICE
            )

            outputs = model(
                images
            )

            loss_bce = bce_loss(
                outputs,
                masks
            )

            loss_dice = dice_loss(
                outputs,
                masks
            )

            loss = (
                0.5 * loss_bce
                + 0.5 * loss_dice
            )

            val_loss_total += (
                loss.item()
                * images.size(0)
            )

            val_count += images.size(0)

            dice_total += (
                dice_score(
                    outputs,
                    masks,
                    threshold=0.5
                )
                * images.size(0)
            )

    val_loss = (
        val_loss_total
        / val_count
    )

    val_dice = (
        dice_total
        / val_count
    )

    # LEARNING RATE

    scheduler.step(
        val_dice
    )

    current_lr = optimizer.param_groups[
        0
    ]["lr"]

    # DISPLAY

    print()
    print(
        f"Epoch {epoch}/{EPOCHS}"
    )

    print(
        f"Train Loss      : {train_loss:.4f}"
    )

    print(
        f"Validation Loss : {val_loss:.4f}"
    )

    print(
        f"Validation Dice : {val_dice:.4f}"
    )

    print(
        f"Learning Rate   : {current_lr:.7f}"
    )

    # SAVE BEST MODEL

    if val_dice > best_dice:

        best_dice = val_dice

        best_epoch = epoch

        patience_counter = 0

        torch.save(
            {
                "model_state_dict":
                    model.state_dict(),

                "epoch":
                    epoch,

                "validation_dice":
                    best_dice
            },
            MODEL_PATH
        )

        print(
            "✓ Best model saved"
        )

    else:

        patience_counter += 1

        print(
            f"No improvement "
            f"({patience_counter}/"
            f"{EARLY_STOPPING_PATIENCE})"
        )

    # EARLY STOPPING

    if (
        patience_counter
        >= EARLY_STOPPING_PATIENCE
    ):

        print()
        print(
            "Early stopping triggered."
        )

        break

# LOAD BEST MODEL

print()
print("=" * 70)
print("LOADING BEST MODEL")
print("=" * 70)

checkpoint = torch.load(
    MODEL_PATH,
    map_location=DEVICE,
    weights_only=False
)

model.load_state_dict(
    checkpoint["model_state_dict"]
)

model.eval()

print(
    f"Best epoch : {checkpoint['epoch']}"
)

print(
    f"Best Dice  : "
    f"{checkpoint['validation_dice']:.4f}"
)

# FIND BEST SEGMENTATION THRESHOLD

print()
print("=" * 70)
print("FINDING BEST SEGMENTATION THRESHOLD")
print("=" * 70)

thresholds = [
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
    0.55,
    0.60,
    0.65,
    0.70
]

threshold_scores = {}

with torch.no_grad():

    for threshold in thresholds:

        total_dice = 0.0

        total_samples = 0

        for images, masks in val_loader:

            images = images.to(
                DEVICE
            )

            masks = masks.to(
                DEVICE
            )

            outputs = model(
                images
            )

            score = dice_score(
                outputs,
                masks,
                threshold=threshold
            )

            total_dice += (
                score
                * images.size(0)
            )

            total_samples += (
                images.size(0)
            )

        average_dice = (
            total_dice
            / total_samples
        )

        threshold_scores[
            threshold
        ] = average_dice

        print(
            f"Threshold {threshold:.2f}"
            f" -> Dice {average_dice:.4f}"
        )


best_threshold = max(
    threshold_scores,
    key=threshold_scores.get
)

best_threshold_dice = threshold_scores[
    best_threshold
]

# SAVE THRESHOLD

with open(
    THRESHOLD_PATH,
    "w"
) as file:

    file.write(
        str(best_threshold)
    )

# FINAL RESULTS

print()
print("=" * 70)
print("TRAINING COMPLETED")
print("=" * 70)

print(
    f"Best validation Dice : "
    f"{best_dice:.4f}"
)

print(
    f"Best epoch           : "
    f"{best_epoch}"
)

print(
    f"Best threshold       : "
    f"{best_threshold:.2f}"
)

print(
    f"Threshold Dice       : "
    f"{best_threshold_dice:.4f}"
)

print()
print(
    f"Model saved to:"
)

print(
    MODEL_PATH
)

print()
print(
    f"Threshold saved to:"
)

print(
    THRESHOLD_PATH
)

print()
print(
    "U-Net training completed successfully."
)