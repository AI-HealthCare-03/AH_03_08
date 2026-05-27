# ai_worker/tasks/image_task.py

# 로컬 모듈
from ai_worker.celery_app import celery_app
from ai_worker.core.config import Config
from ai_worker.core.logger import logger
from ai_worker.image import get_image_classifier

config = Config()


# DB 초기화
_tortoise_initialized = False


async def _init_tortoise():
    global _tortoise_initialized
    if _tortoise_initialized:
        return
    from tortoise import Tortoise

    await Tortoise.init(
        db_url=(f"mysql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"),
        modules={"models": ["ai_worker.models"]},
    )
    _tortoise_initialized = True


def _run_async(coro):
    import asyncio

    global _tortoise_initialized
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _tortoise_initialized = False
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            from tortoise import Tortoise

            loop.run_until_complete(Tortoise.close_connections())
        except Exception:
            pass
        loop.close()
        asyncio.set_event_loop(None)


async def _save_image_result(record_id: str, drug_info: dict):
    await _init_tortoise()
    from ai_worker.models import MedicalRecord

    await MedicalRecord.filter(id=record_id).update(
        parsed_data=drug_info,
        status="COMPLETED",
    )


async def _save_failed_result(record_id: str):
    await _init_tortoise()
    from ai_worker.models import MedicalRecord

    await MedicalRecord.filter(id=record_id).update(
        status="FAILED",
    )


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

        classifier = get_image_classifier(config)
        kcode, drug_info, confidence_score = classifier.classify(image_bytes)

        if confidence_score < 0.7:
            logger.warning(f"분류 불가 - confidence: {confidence_score:.4f}")
            _run_async(_save_failed_result(record_id))
            return {
                "success": False,
                "data": None,
                "message": "분류할 수 없는 약품입니다.",
            }

        drug_info["confidence_score"] = confidence_score
        _run_async(_save_image_result(record_id, drug_info))
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
