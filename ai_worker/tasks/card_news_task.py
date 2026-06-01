from celery.utils.log import get_task_logger

from ai_worker.card_news import get_card_news_generator
from ai_worker.celery_app import celery_app
from ai_worker.core.config import Config

logger = get_task_logger(__name__)
config = Config()


@celery_app.task(
    bind=True,
    name="ai_worker.tasks.card_news_task.generate_card_news_task",
    max_retries=3,
)
def generate_card_news_task(self, asset_id: str, guide_id: str, text: str, user_id: str) -> dict:
    """가이드 요약 텍스트로 카드뉴스 이미지를 생성하고 S3에 저장한다.

    Args:
        asset_id: GUIDE_ASSETS 테이블의 asset_id
        guide_id: GUIDES 테이블의 guide_id
        text: 변환할 텍스트 (GUIDES.summary_text)
        user_id: 요청한 사용자 ID (S3 경로 구분용)

    Returns:
        dict: { "success": bool, "data": { "s3_url": str }, "message": str }

    Note:
        - 개인정보 보호: 의료 데이터(text) 로그 직접 출력 금지
    """
    try:
        logger.info(f"카드뉴스 생성 시작 - guide_id: {guide_id}, asset_id: {asset_id}")

        generator = get_card_news_generator(config)
        image_data = generator.generate(text)
        s3_url = generator.upload_to_s3(image_data, user_id)

        logger.info(f"카드뉴스 생성 완료 - guide_id: {guide_id}")
        return {
            "success": True,
            "data": {
                "guide_id": guide_id,
                "asset_id": asset_id,
                "s3_url": s3_url,
            },
            "message": "카드뉴스 생성이 완료되었습니다.",
        }
    except Exception as exc:
        logger.error(f"카드뉴스 생성 실패 - guide_id: {guide_id}, error: {exc}")
        raise self.retry(exc=exc, countdown=10) from exc