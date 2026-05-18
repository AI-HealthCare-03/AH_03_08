# 표준 라이브러리
import io

# 서드파티 라이브러리
import torch
from PIL import Image
from torchvision import transforms

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