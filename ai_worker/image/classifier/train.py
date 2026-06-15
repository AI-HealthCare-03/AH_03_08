# ai_worker/image/classifier/train.py

import csv
import os

import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

# ── 설정 ──────────────────────────────────────────────
KAGGLE_IMG_BASE = "/kaggle/input/datasets/jayjun/pill-image/pill_image"
TRAIN_CSV = "/kaggle/input/datasets/jayjun/pill-image/train.csv"
VAL_CSV = "/kaggle/input/datasets/jayjun/pill-image/val.csv"
EPOCHS = 20
BATCH_SIZE = 32
LR = 1e-4
NUM_WORKERS = 2
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
COLOR_CLASSES = ["갈색", "검정", "노랑", "보라", "분홍", "빨강", "연두", "주황", "청록", "초록", "파랑", "하양", "회색"]
SHAPE_CLASSES = ["기타", "마름모형", "사각형", "삼각형", "오각형", "원형", "육각형", "장방형", "타원형", "팔각형"]


# ── 데이터셋 ──────────────────────────────────────────
class PillDataset(Dataset):
    def __init__(self, csv_path, transform=None):
        self.data = []
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                color = row["color"]
                shape = row["shape"]
                if color in COLOR_CLASSES and shape in SHAPE_CLASSES:
                    self.data.append(
                        (
                            row["image_path"],
                            COLOR_CLASSES.index(color),
                            SHAPE_CLASSES.index(shape),
                        )
                    )
        self.transform = transform

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        img_path, color_label, shape_label = self.data[idx]
        # 파일명만 추출해서 Kaggle 경로로 재조합
        filename = os.path.basename(img_path)
        drug_dir = os.path.basename(os.path.dirname(img_path))
        kaggle_path = os.path.join(KAGGLE_IMG_BASE, drug_dir, filename)
        image = Image.open(kaggle_path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, color_label, shape_label


# ── 모델 ──────────────────────────────────────────────
class ColorShapeClassifier(nn.Module):
    def __init__(self, num_colors, num_shapes):
        super().__init__()
        backbone = models.mobilenet_v2(weights="IMAGENET1K_V1")
        self.features = backbone.features
        self.pool = nn.AdaptiveAvgPool2d(1)
        in_features = backbone.classifier[1].in_features
        self.color_head = nn.Linear(in_features, num_colors)
        self.shape_head = nn.Linear(in_features, num_shapes)

    def forward(self, x):
        x = self.features(x)
        x = self.pool(x)
        x = x.flatten(1)
        return self.color_head(x), self.shape_head(x)


# ── 학습 ──────────────────────────────────────────────
def train():
    transform_train = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(30),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    transform_val = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    train_dataset = PillDataset(TRAIN_CSV, transform_train)
    val_dataset = PillDataset(VAL_CSV, transform_val)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)

    model = ColorShapeClassifier(len(COLOR_CLASSES), len(SHAPE_CLASSES)).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

    best_val_acc = 0.0

    for epoch in range(EPOCHS):
        # 학습
        model.train()
        train_loss = 0.0
        for images, color_labels, shape_labels in train_loader:
            images = images.to(DEVICE)
            color_labels = color_labels.to(DEVICE)
            shape_labels = shape_labels.to(DEVICE)

            color_out, shape_out = model(images)
            loss = criterion(color_out, color_labels) + criterion(shape_out, shape_labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        # 검증
        model.eval()
        color_correct = shape_correct = total = 0
        all_color_preds, all_color_labels = [], []
        all_shape_preds, all_shape_labels = [], []

        with torch.no_grad():
            for images, color_labels, shape_labels in val_loader:
                images = images.to(DEVICE)
                color_labels = color_labels.to(DEVICE)
                shape_labels = shape_labels.to(DEVICE)

                color_out, shape_out = model(images)
                color_preds = color_out.argmax(dim=1)
                shape_preds = shape_out.argmax(dim=1)

                color_correct += (color_preds == color_labels).sum().item()
                shape_correct += (shape_preds == shape_labels).sum().item()
                total += images.size(0)

                all_color_preds.extend(color_preds.cpu().numpy())
                all_color_labels.extend(color_labels.cpu().numpy())
                all_shape_preds.extend(shape_preds.cpu().numpy())
                all_shape_labels.extend(shape_labels.cpu().numpy())

        color_acc = color_correct / total
        shape_acc = shape_correct / total
        color_f1 = f1_score(all_color_labels, all_color_preds, average="macro")
        shape_f1 = f1_score(all_shape_labels, all_shape_preds, average="macro")
        avg_acc = (color_acc + shape_acc) / 2

        print(
            f"Epoch {epoch + 1}/{EPOCHS} | loss: {train_loss / len(train_loader):.4f} | "
            f"color_acc: {color_acc:.4f} | shape_acc: {shape_acc:.4f} | "
            f"color_f1: {color_f1:.4f} | shape_f1: {shape_f1:.4f}"
        )

        if avg_acc > best_val_acc:
            best_val_acc = avg_acc
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "color_classes": COLOR_CLASSES,
                    "shape_classes": SHAPE_CLASSES,
                },
                "color_shape_model.pt",
            )
            print(f"  → 모델 저장 (best avg_acc: {best_val_acc:.4f})")

        scheduler.step()


train()
