# app/services/tts.py

# 표준 라이브러리
import uuid

# 로컬 모듈
from ai_worker.tasks.tts_task import convert_text_to_speech

# 서드파티 라이브러리
from fastapi.exceptions import HTTPException
from starlette import status

from app.dtos.tts import AssetType, GuideAssetCreateResponse


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

        REQ-GUIDE-002 연동: GUIDES 테이블의 요약본 텍스트를
        CLOVA TTS로 변환 후 S3에 저장한다. (asset_type=tts)

        Args:
            guide_id: GUIDES 테이블의 guide_id
            asset_type: "tts" or "card_image"
            user_id: 요청한 사용자 ID
            summary_text: GUIDES.medication_guide 또는 GUIDES.lifestyle_guide

        Returns:
            GuideAssetCreateResponse: { asset_id, status }

        Note:
            - 개인정보 보호: 의료 데이터(summary_text) 로그 직접 출력 금지
        """
        # asset_type 검증
        if asset_type != AssetType.tts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="가이드가 생성되지 않은 상태입니다.",
            )

        # 고유한 asset_id 생성
        asset_id = str(uuid.uuid4())

        # Celery Task 등록 → 즉시 반환 (백그라운드에서 처리)
        # .delay() → Redis에 작업 등록 후 바로 반환
        convert_text_to_speech.delay(
            guide_id=guide_id,
            summary_text=summary_text,
            user_id=user_id,
        )

        # API 명세서: { "asset_id": uuid, "status": "processing" }
        return GuideAssetCreateResponse(
            asset_id=asset_id,
            status="processing",
        )
