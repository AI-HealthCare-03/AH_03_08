# ai_worker/image/classifier/model.py

import io

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

COLOR_CLASSES = ["갈색", "검정", "노랑", "보라", "분홍", "빨강", "연두", "주황", "청록", "초록", "파랑", "하양", "회색"]
SHAPE_CLASSES = ["기타", "마름모형", "사각형", "삼각형", "오각형", "원형", "육각형", "장방형", "타원형", "팔각형"]


class ColorShapeClassifier(nn.Module):
    def __init__(self, num_colors, num_shapes):
        super().__init__()
        backbone = models.mobilenet_v2(weights=None)
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


def load_color_shape_model(model_path: str) -> tuple:
    """
    학습된 색상/모양 분류 모델을 로드한다.

    Returns:
        tuple: (model, color_classes, shape_classes)
    """
    checkpoint = torch.load(model_path, map_location="cpu")
    color_classes = checkpoint.get("color_classes", COLOR_CLASSES)
    shape_classes = checkpoint.get("shape_classes", SHAPE_CLASSES)

    model = ColorShapeClassifier(len(color_classes), len(shape_classes))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    return model, color_classes, shape_classes


def predict_color_shape(
    model: nn.Module,
    image_bytes: bytes,
    color_classes: list[str],
    shape_classes: list[str],
) -> tuple[str, str, float, float]:
    """
    이미지에서 색상과 모양을 예측한다.

    Args:
        model: 로드된 ColorShapeClassifier
        image_bytes: 업로드된 이미지 bytes
        color_classes: 색상 클래스 목록
        shape_classes: 모양 클래스 목록

    Returns:
        tuple: (predicted_color, predicted_shape, color_confidence, shape_confidence)
    """
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        color_out, shape_out = model(tensor)
        color_probs = torch.softmax(color_out, dim=1)
        shape_probs = torch.softmax(shape_out, dim=1)

        color_conf, color_idx = torch.max(color_probs, dim=1)
        shape_conf, shape_idx = torch.max(shape_probs, dim=1)

    predicted_color = color_classes[color_idx.item()]
    predicted_shape = shape_classes[shape_idx.item()]
    color_confidence = color_conf.item()
    shape_confidence = shape_conf.item()

    return predicted_color, predicted_shape, color_confidence, shape_confidence
