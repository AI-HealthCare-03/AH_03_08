# app/services/tts.py

# 표준 라이브러리
import uuid

# 서드파티 라이브러리
from celery import Celery
from fastapi.exceptions import HTTPException
from starlette import status

# 로컬 모듈
from app.core.config import config
from app.dtos.tts import AssetType, GuideAssetCreateResponse

celery_app = Celery(broker=config.CELERY_BROKER_URL, backend=config.CELERY_RESULT_BACKEND)


class TtsService:
    async def create_guide_asset(
        self,
        guide_id: str,
        asset_type: AssetType,
        user_id: str,
        summary_text: str,
    ) -> GuideAssetCreateResponse:
        """
        가이드 에셋 생성 요청을 처리하고 Celery Task를 등록한다.

        Args:
            guide_id: GUIDES 테이블의 guide_id
            asset_type: "tts_medication" 또는 "tts_lifestyle"
            user_id: 요청한 사용자 ID
            summary_text: GUIDES.medication_guide_summary 또는 GUIDES.lifestyle_guide_summary

        Returns:
            GuideAssetCreateResponse: { asset_id, status }

        Note:
            - 개인정보 보호: 의료 데이터(summary_text) 로그 직접 출력 금지
            - app과 ai_worker가 별도 컨테이너라 send_task()로 Redis에 등록
        """
        if asset_type not in (AssetType.tts_medication, AssetType.tts_lifestyle):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="지원하지 않는 asset_type입니다.",
            )

        asset_id = str(uuid.uuid4())

        celery_app.send_task(
            "ai_worker.task.tts_task.generate_tts_task",
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
