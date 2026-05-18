# 표준 라이브러리
import io
import json
import glob
import os

# 서드파티 라이브러리
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

# 로거 설정
from ai_worker.core.logger import logger


# -------------------------
# 이미지 전처리
# -------------------------

def preprocess_image(image_bytes: bytes) -> torch.Tensor:
    """
    사용자가 업로드한 이미지를 ResNet152 모델 입력 형식으로 변환한다.

    REQ-IMG-001: 이미지 전처리
    - 224x224 리사이즈
    - Normalize 적용 (ImageNet mean/std)

    Args:
        image_bytes: 사용자가 업로드한 이미지 파일 (bytes)

    Returns:
        torch.Tensor: 모델 입력 가능한 텐서 (1, 3, 224, 224)

    Note:
        - 개인정보 보호: 이미지 데이터 로그 출력 금지
        - mean/std는 ImageNet 학습 기준값 사용
    """
    # 전처리 파이프라인 정의
    transform = transforms.Compose([
        transforms.Resize((224, 224)),       # 모델 입력 크기로 리사이즈
        transforms.ToTensor(),               # PIL Image → Tensor (0~255 → 0~1)
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],      # ImageNet 평균값
            std=[0.229, 0.224, 0.225],       # ImageNet 표준편차
        ),
    ])

    # bytes → PIL Image 변환
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # 전처리 적용 후 배치 차원 추가 (3, 224, 224) → (1, 3, 224, 224)
    tensor = transform(image).unsqueeze(0)

    logger.info(f"이미지 전처리 완료 - tensor shape: {tensor.shape}")

    return tensor

# -------------------------
# 모델 로드 (REQ-IMG-002)
# -------------------------

def load_model() -> nn.Module:
    """
    ResNet152 모델을 로드한다.

    Returns:
        nn.Module: 로드된 ResNet152 모델

    Note:
        - 모델 파일 경로는 반드시 .env에서 관리 (하드코딩 금지)
        - CPU 환경에서 로드 (map_location="cpu")
    """
    model_path = os.getenv("PILL_MODEL_PATH")

    if not model_path:
        raise ValueError("PILL_MODEL_PATH 환경변수가 설정되지 않았습니다.")

    # ResNet152 구조 초기화
    model = models.resnet152(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 1000)  # 1000개 클래스

    # 학습된 가중치 로드
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()  # 추론 모드

    logger.info("ResNet152 모델 로드 완료")
    return model


# -------------------------
# 모델 추론 (REQ-IMG-002)
# -------------------------

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

    logger.info(f"모델 추론 완료 - class_idx: {class_idx}, confidence: {confidence_score:.4f}")

    return class_idx, confidence_score


# -------------------------
# K코드 변환 (REQ-IMG-003)
# -------------------------

def get_kcode(class_idx: int) -> str:
    """
    클래스 인덱스를 K코드로 변환한다.

    Args:
        class_idx: 모델 출력 클래스 인덱스 (0~999)

    Returns:
        str: K코드 (예: "K-037589")
    """
    label_path = os.getenv("PILL_LABEL_PATH")

    if not label_path:
        raise ValueError("PILL_LABEL_PATH 환경변수가 설정되지 않았습니다.")

    with open(label_path, "r") as f:
        data = json.load(f)

    # 인덱스 → K코드 매핑
    index_to_kcode = {item[0]: item[1] for item in data["pill_label_path_sharp_score"]}

    kcode = index_to_kcode.get(class_idx)
    if not kcode:
        raise ValueError(f"클래스 인덱스 {class_idx}에 해당하는 K코드가 없습니다.")

    logger.info(f"K코드 변환 완료 - class_idx: {class_idx} → kcode: {kcode}")
    return kcode


# -------------------------
# 약품 정보 조회 (REQ-IMG-004)
# -------------------------

def get_drug_info(kcode: str) -> dict:
    """
    K코드로 AI Hub JSON DB에서 약품 정보를 조회한다.

    Args:
        kcode: K코드 (예: "K-037589")

    Returns:
        dict: 약품 상세 정보

    Note:
        - 개인정보 보호: 약품 정보 조회 시 K코드만 로그 기록
    """
    data_path = os.getenv("PILL_DATA_PATH")

    if not data_path:
        raise ValueError("PILL_DATA_PATH 환경변수가 설정되지 않았습니다.")

    # K코드 폴더에서 json 파일 탐색
    # TODO: EC2 배포 시 S3에서 데이터셋 조회하는 방식으로 교체
    json_files = glob.glob(f"{data_path}/{kcode}/*.json")

    if not json_files:
        raise ValueError(f"K코드 {kcode}에 해당하는 약품 정보가 없습니다.")

    with open(json_files[0], "r", encoding="utf-8") as f:
        data = json.load(f)

    info = data["images"][0]

    logger.info(f"약품 정보 조회 완료 - kcode: {kcode}")

    return {
        "drug_name": info.get("dl_name"),
        "dl_material": info.get("dl_material"),
        "drug_shape": info.get("drug_shape"),
        "color_class1": info.get("color_class1"),
        "di_class_no": info.get("di_class_no"),
        "di_etc_otc_code": info.get("di_etc_otc_code"),
        "di_edi_code": info.get("di_edi_code"),
    }