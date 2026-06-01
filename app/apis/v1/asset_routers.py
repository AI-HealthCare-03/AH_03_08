# app/apis/v1/asset_routers.py

# 표준 라이브러리
from typing import Annotated

# 서드파티 라이브러리
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse as Response

# 로컬 모듈
from app.dependencies.security import get_request_user
from app.dtos.asset import AssetType, GuideAssetCreateRequest, GuideAssetCreateResponse
from app.models.guides import Guide
from app.models.users import User
from app.services.card_news import CardNewsService
from app.services.tts import TtsService

asset_router = APIRouter(prefix="/guides", tags=["guides"])


@asset_router.post(
    "/{guide_id}/assets",
    response_model=GuideAssetCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_guide_asset(
    guide_id: str,
    request: GuideAssetCreateRequest,
    tts_service: Annotated[TtsService, Depends(TtsService)],
    card_news_service: Annotated[CardNewsService, Depends(CardNewsService)],
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """
    TTS 음성 / 카드뉴스 이미지 생성 요청 엔드포인트.

    API 명세서: POST /api/v1/guides/{guide_id}/assets
    REQ-GUIDE-002 연동 (asset_type=tts, asset_type=card_news)

    Args:
        guide_id: GUIDES 테이블의 guide_id
        request: { asset_type: "tts" or "card_news" }
        current_user: JWT 인증된 사용자 (Bearer token)

    Returns:
        202 Accepted: { asset_id, status: "processing" }

    Note:
        - 개인정보 보호: 의료 데이터 접근 시 JWT 인증 필수
        - Celery Task 등록 후 즉시 202 반환 (비동기 처리)
    """
    guide = await Guide.get_or_none(id=guide_id, user_id=current_user.id)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="가이드를 찾을 수 없습니다.")
    summary_text = guide.summary_text or ""

    if request.asset_type == AssetType.tts:
        result = await tts_service.create_tts_asset(
            guide_id=guide_id,
            user_id=str(current_user.id),
            summary_text=summary_text,
        )
    elif request.asset_type == AssetType.card_news:
        result = await card_news_service.create_card_news_asset(
            guide_id=guide_id,
            user_id=str(current_user.id),
            summary_text=summary_text,
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="지원하지 않는 asset_type입니다.")

    return Response(
        content=result.model_dump(),
        status_code=status.HTTP_202_ACCEPTED,
    )
