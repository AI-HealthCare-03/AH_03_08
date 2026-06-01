# app/services/tts.py

# 표준 라이브러리
import uuid

# 서드파티 라이브러리
from celery import Celery

# 로컬 모듈
from app.core.config import config
from app.dtos.asset import GuideAssetCreateResponse

celery_app = Celery(broker=config.CELERY_BROKER_URL, backend=config.CELERY_RESULT_BACKEND)


class TtsService:
    async def create_tts_asset(
        self,
        guide_id: str,
        user_id: str,
        summary_text: str,
    ) -> GuideAssetCreateResponse:
        """
        TTS 음성 변환 요청을 처리하고 Celery Task를 등록한다.

        Args:
            guide_id: GUIDES 테이블의 guide_id
            user_id: 요청한 사용자 ID
            summary_text: GUIDES.summary_text (복약+생활 통합 요약)

        Returns:
            GuideAssetCreateResponse: { asset_id, status }

        Note:
            - 개인정보 보호: 의료 데이터(summary_text) 로그 직접 출력 금지
            - app과 ai_worker가 별도 컨테이너라 send_task()로 Redis에 등록
        """
        asset_id = str(uuid.uuid4())

        celery_app.send_task(
            "ai_worker.tasks.tts_task.generate_tts_task",
            kwargs={
                "asset_id": asset_id,
                "guide_id": guide_id,
                "text": summary_text,
                "user_id": user_id,
            },
        )
        return GuideAssetCreateResponse(
            asset_id=asset_id,
            status="processing",
        )
