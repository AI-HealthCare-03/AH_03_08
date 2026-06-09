# app/apis/v1/asset_routers.py

# 표준 라이브러리
from typing import Annotated

# 서드파티 라이브러리
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

# 로컬 모듈
from app.dependencies.security import get_request_user
from app.dtos.asset import AssetType, GuideAssetCreateRequest
from app.models.guide import Guide
from app.models.users import User
from app.services.card_news import CardNewsService

asset_router = APIRouter(prefix="/guides", tags=["guides"])


@asset_router.post(
    "/{guide_id}/assets",
    status_code=status.HTTP_200_OK,
)
async def create_guide_asset(
    guide_id: str,
    request: GuideAssetCreateRequest,
    card_news_service: Annotated[CardNewsService, Depends(CardNewsService)],
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """
    카드뉴스 이미지 생성 엔드포인트.

    API 명세서: POST /api/v1/guides/{guide_id}/assets
    REQ-GUIDE-002 연동 (asset_type=card_news)

    Args:
        guide_id: GUIDES 테이블의 guide_id
        request: { asset_type: "card_news" }
        current_user: JWT 인증된 사용자 (Bearer token)

    Returns:
        200 OK: png bytes (card_news)

    Note:
        - 개인정보 보호: 의료 데이터 접근 시 JWT 인증 필수
        - S3 저장 없이 bytes 즉시 반환
    """
    guide = await Guide.get_or_none(id=guide_id, user_id=current_user.id)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="가이드를 찾을 수 없습니다.")
    summary_text = guide.summary_text or ""

    if request.asset_type == AssetType.card_news:
        from app.models.medical_records import MedicalRecord

        record = await MedicalRecord.get_or_none(id=guide.record_id)
        medications = (record.parsed_data or {}).get("medications", []) if record else []

        image_bytes = await card_news_service.create_card_news_asset(
            summary_text=summary_text,
            medication_guide=guide.medication_guide,
            lifestyle_guide=guide.lifestyle_guide,
            medications=medications,
        )

        return Response(content=image_bytes, media_type="image/png")

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="지원하지 않는 asset_type입니다.")