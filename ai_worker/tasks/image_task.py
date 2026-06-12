# ai_worker/tasks/image_task.py
#
# torchvision/torch import를 모듈 최상단에서 하지 않는다.
# llm-worker(-Q llm)가 이 파일을 include할 때 torchvision이 로드되면
# CPU 빌드에서 RuntimeError: operator torchvision::nms does not exist 발생.
# PillClassifier, get_image_classifier는 실제 사용 시점(_load_classifier)에만 import.
import asyncio
import base64

from celery.signals import worker_process_init, worker_process_shutdown

from ai_worker.celery_app import celery_app
from ai_worker.core.config import Config
from ai_worker.core.logger import logger

config = Config()

_classifier = None


@worker_process_init.connect
def _load_classifier(**kwargs) -> None:
    """워커 프로세스 시작 시 ResNet152 모델을 1회 로드한다."""
    global _classifier
    try:
        from ai_worker.image import get_image_classifier

        _classifier = get_image_classifier(config)
        logger.info("PillClassifier 초기화 완료 (프로세스 시작 시 1회 로드)")
    except Exception as exc:
        logger.warning(f"PillClassifier 초기화 실패 (PILL_MODEL_PATH 확인 필요): {exc}")


@worker_process_shutdown.connect
def _unload_classifier(**kwargs) -> None:
    """워커 프로세스 종료 시 메모리 해제."""
    global _classifier
    _classifier = None
    logger.info("PillClassifier 메모리 해제")


def _get_classifier():
    """싱글톤 반환. 초기화 실패 상태면 즉시 재시도."""
    global _classifier
    if _classifier is None:
        from ai_worker.image import get_image_classifier

        _classifier = get_image_classifier(config)
    return _classifier


def _run_ocr(image_bytes: bytes) -> list[str]:
    """CLOVA OCR을 동기 컨텍스트에서 실행한다."""
    try:
        from ai_worker.ocr.clova import ClovaOCRProvider

        if not config.CLOVA_OCR_URL or not config.CLOVA_OCR_SECRET:
            return []

        ocr = ClovaOCRProvider(url=config.CLOVA_OCR_URL, secret=config.CLOVA_OCR_SECRET)
        return asyncio.run(ocr.extract_text_from_bytes(image_bytes))
    except Exception as exc:
        logger.warning(f"OCR 실행 실패: {exc}")
        return []


@celery_app.task(
    bind=True,
    name="ai_worker.tasks.image_task.classify_pill",
    max_retries=3,
)
def classify_pill(self, image_bytes: str, record_id: str, user_id: str) -> dict:
    """
    낱알약 이미지를 분류하는 Celery Task.

    Args:
        image_bytes: 사용자가 업로드한 이미지 파일 (base64 인코딩된 str)
        record_id: MEDICAL_RECORDS 테이블의 record_id (FK)
        user_id: 요청한 사용자 ID

    Returns:
        dict: { "success": bool, "data": { "drug_info": dict }, "message": str }

    Note:
        - 개인정보 보호: 이미지 데이터 로그 출력 금지
        - Threshold 0.7 미만 시 분류 불가 처리
    """
    try:
        logger.info(f"낱알약 분류 시작 - record_id: {record_id}")

        classifier = _get_classifier()

        if isinstance(image_bytes, str):
            image_bytes = base64.b64decode(image_bytes)

        # CLOVA OCR 실행
        ocr_texts = _run_ocr(image_bytes)
        logger.info(f"OCR 추출 텍스트: {ocr_texts}")

        # OCR 결과 활용하여 분류
        kcode, drug_info, confidence_score, method, candidates = classifier.classify_with_ocr(image_bytes, ocr_texts)
        logger.info(f"분류 방법: {method}, kcode: {kcode}, confidence: {confidence_score:.4f}")

        from ai_worker.callback import image_done, image_failed

        # OCR 매칭 실패 + ResNet152 confidence 낮은 경우
        if method == "resnet" and confidence_score < 0.7:
            logger.warning(f"분류 불가 - confidence: {confidence_score:.4f}")
            image_failed(record_id)
            return {
                "success": False,
                "data": None,
                "message": "분류할 수 없는 약품입니다.",
            }

        drug_info["confidence_score"] = confidence_score

        parsed_data = {
            "medications": [
                {
                    "name": drug_info.get("drug_name"),
                    "dosage": None,
                    "frequency": None,
                    "duration": None,
                    "instructions": drug_info.get("dl_material"),
                    "category": drug_info.get("di_class_no"),
                    "otc_code": drug_info.get("di_etc_otc_code"),
                }
            ],
            "drug_info": drug_info,
            "ocr_texts": ocr_texts,  # 프론트 확인 화면에서 활용
            "candidates": candidates,  # 추가
        }
        image_done(record_id, parsed_data)
        logger.info(f"낱알약 분류 완료 - kcode: {kcode}, method: {method}")

        return {
            "success": True,
            "data": {
                "kcode": kcode,
                "drug_info": drug_info,
                "ocr_texts": ocr_texts,
                "method": method,
                "candidates": candidates,  # 추가
            },
            "message": "낱알약 분류가 완료되었습니다." if not candidates else "복수 후보가 있습니다. 약품명을 확인해 주세요.",
        }

    except Exception as exc:
        logger.error(f"낱알약 분류 실패 - record_id: {record_id}, error: {exc}")
        raise self.retry(exc=exc, countdown=10) from exc
