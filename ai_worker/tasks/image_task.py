# ai_worker/tasks/image_task.py
#
# torchvision/torch import를 모듈 최상단에서 하지 않는다.
# llm-worker(-Q llm)가 이 파일을 include할 때 torchvision이 로드되면
# CPU 빌드에서 RuntimeError: operator torchvision::nms does not exist 발생.
# PillClassifier, get_image_classifier는 실제 사용 시점(_load_classifier)에만 import.

from celery.signals import worker_process_init, worker_process_shutdown

from ai_worker.celery_app import celery_app
from ai_worker.core.config import Config
from ai_worker.core.logger import logger

config = Config()

# ─────────────────────────────────────────────────────────────────
# [최적화 5] PillClassifier 프로세스 레벨 싱글톤
#
# 문제: 기존 classify_pill()은 호출마다 get_image_classifier()를 실행,
#       ResNet152 모델(수백 MB)을 매번 디스크에서 로드 → 태스크당 수 초 지연.
#
# 해결: worker_process_init 시그널로 워커 프로세스 시작 시 1회만 로드.
#       이후 태스크는 이미 메모리에 올라간 인스턴스를 바로 사용.
#
# concurrency=2 기준: 프로세스 2개 × 1회 로드 = 총 2회 로드 (이전: 요청마다)
# ─────────────────────────────────────────────────────────────────
_classifier = None  # PillClassifier | None (lazy import로 타입 명시 생략)


@worker_process_init.connect
def _load_classifier(**kwargs) -> None:
    """워커 프로세스 시작 시 ResNet152 모델을 1회 로드한다."""
    global _classifier
    try:
        from ai_worker.image import get_image_classifier  # lazy import — llm-worker 로드 시 torchvision 방지
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
        from ai_worker.image import get_image_classifier  # lazy import
        _classifier = get_image_classifier(config)
    return _classifier

@celery_app.task(
    bind=True,
    name="ai_worker.tasks.image_task.classify_pill",
    max_retries=3,
)
def classify_pill(self, image_bytes: bytes, record_id: str, user_id: str) -> dict:
    """
    낱알약 이미지를 분류하는 Celery Task.

    Args:
        image_bytes: 사용자가 업로드한 이미지 파일 (bytes)
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

        # [최적화 5] 싱글톤에서 이미 로드된 분류기 반환 (모델 재로드 없음)
        classifier = _get_classifier()
        kcode, drug_info, confidence_score = classifier.classify(image_bytes)

        # [12] DB 저장 책임을 FastAPI에 위임
        from ai_worker.callback import image_done, image_failed

        if confidence_score < 0.7:
            logger.warning(f"분류 불가 - confidence: {confidence_score:.4f}")
            image_failed(record_id)
            return {
                "success": False,
                "data": None,
                "message": "분류할 수 없는 약품입니다.",
            }

        drug_info["confidence_score"] = confidence_score

        # medications 구조로 감싸서 저장
        parsed_data = {
            "medications": [{
                "name": drug_info.get("drug_name"),
                "instructions": drug_info.get("dl_material"),
            }],
            "drug_info": drug_info  # 원본 보존 (카드뉴스용)
        }
        image_done(record_id, parsed_data)
        logger.info(f"낱알약 분류 완료 - kcode: {kcode}")

        return {
            "success": True,
            "data": {
                "kcode": kcode,
                "drug_info": drug_info,
            },
            "message": "낱알약 분류가 완료되었습니다.",
        }

    except Exception as exc:
        logger.error(f"낱알약 분류 실패 - record_id: {record_id}, error: {exc}")
        raise self.retry(exc=exc, countdown=10) from exc
