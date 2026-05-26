import asyncio

from celery.utils.log import get_task_logger

from ai_worker.celery_app import celery_app
from ai_worker.core.config import Config
from ai_worker.tts import get_tts_provider

logger = get_task_logger(__name__)
config = Config()


@celery_app.task(
    bind=True,
    name="ai_worker.tasks.tts_task.generate_tts_task",
    max_retries=3,
)
def generate_tts_task(self, asset_id: str, guide_id: str, text: str, user_id: str) -> dict:
    """가이드 텍스트를 TTS로 변환하고 S3에 저장한다.

    Args:
        asset_id: GUIDE_ASSETS 테이블의 asset_id
        guide_id: GUIDES 테이블의 guide_id
        text: 변환할 텍스트
        user_id: 요청한 사용자 ID (S3 경로 구분용)

    Returns:
        dict: { "success": bool, "data": { "s3_url": str }, "message": str }

    Note:
        - 개인정보 보호: 의료 데이터(text) 로그 직접 출력 금지
    """
    try:
        logger.info(f"TTS 변환 시작 - guide_id: {guide_id}, asset_id: {asset_id}")

        provider = get_tts_provider(config)
        audio_data = asyncio.run(provider.convert_text_to_speech(text))
        s3_url = provider.upload_to_s3(audio_data, user_id)

        logger.info(f"TTS 변환 완료 - guide_id: {guide_id}")
        return {
            "success": True,
            "data": {
                "guide_id": guide_id,
                "asset_id": asset_id,
                "s3_url": s3_url,
            },
            "message": "TTS 변환이 완료되었습니다.",
        }
    except Exception as exc:
        logger.error(f"TTS 변환 실패 - guide_id: {guide_id}, error: {exc}")
        raise self.retry(exc=exc, countdown=10) from exc

