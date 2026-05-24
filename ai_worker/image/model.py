# ai_worker/image/model.py

# 표준 라이브러리

# 서드파티 라이브러리
import torch
import torch.nn as nn
from torchvision import models

# 로컬 모듈
from ai_worker.core.logger import logger


def load_model(model_path: str) -> nn.Module:
    """
    ResNet152 모델을 로드한다.

    Args:
        model_path: 모델 파일 경로

    Returns:
        nn.Module: 로드된 ResNet152 모델

    Note:
        - CPU 환경에서 로드 (map_location="cpu")
    """
    if not model_path:
        raise ValueError("PILL_MODEL_PATH 환경변수가 설정되지 않았습니다.")

    model = models.resnet152(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 1000)

    checkpoint = torch.load(model_path, map_location="cpu")
    model.load_state_dict(checkpoint["model"])
    model.eval()

    logger.info("ResNet152 모델 로드 완료")
    return model


def predict(model: nn.Module, tensor: torch.Tensor) -> tuple[int, float]:
    """
    전처리된 이미지 텐서를 모델에 입력하여 클래스 인덱스와 confidence score를 반환한다.

    Args:
        model: 로드된 ResNet152 모델
        tensor: 전처리된 이미지 텐서 (1, 3, 224, 224)

    Returns:
        tuple[int, float]: (클래스 인덱스, confidence score)

    Note:
        - Threshold 0.7 미만 시 분류 불가 처리
    """
    with torch.no_grad():
        outputs = model(tensor)
        probabilities = torch.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probabilities, dim=1)

    class_idx = predicted.item()
    confidence_score = confidence.item()

    top5 = torch.topk(probabilities, k=5, dim=1)
    _top5_log = [
        (idx.item(), round(conf.item(), 4))
        for idx, conf in zip(top5.indices[0], top5.values[0], strict=False)
    ]
    logger.info(f"모델 추론 완료 - class_idx: {class_idx}, confidence: {confidence_score:.4f}")
    logger.info(f"Top-5 추론 결과 (관리자용): {_top5_log}")

    return class_idx, confidence_score