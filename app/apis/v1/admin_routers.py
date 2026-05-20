from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.dependencies.security import get_admin_user
from app.models.guides import Guide
from app.models.users import User
from app.services.feedback_prompt_insights import list_guides_with_many_low_ratings

router = APIRouter(prefix="/admin", tags=["admin"])

AdminUser = Annotated[User, Depends(get_admin_user)]


@router.get("/guides/low-rating-summary")
async def get_guides_with_many_zero_ratings(
    _admin: AdminUser,
    min_low_ratings: int = Query(3, ge=1, description="이 개수 이상의 rating=0 피드백이 있는 가이드만"),
    limit: int = Query(50, ge=1, le=200),
):
    """rating=0 피드백이 많은 가이드와 당시 prompt_version 조회 (프롬프트 개선 트래킹용)."""
    rows = await list_guides_with_many_low_ratings(min_count=min_low_ratings, limit=limit)
    return {
        "success": True,
        "data": {"items": rows, "total": len(rows)},
        "message": "조회 성공",
    }


class PromptVersionBody(BaseModel):
    prompt_version: str = Field(..., max_length=20, description="가이드에 기록할 프롬프트 버전 라벨")


@router.patch("/guides/{guide_id}/prompt-version")
async def patch_guide_prompt_version(guide_id: str, body: PromptVersionBody, _admin: AdminUser):
    """프롬프트 개선 후 해당 가이드(및 추적)에 쓰인 버전 라벨을 갱신한다."""
    guide = await Guide.get_or_none(id=guide_id)
    if not guide:
        raise HTTPException(status_code=404, detail="가이드를 찾을 수 없습니다.")
    guide.prompt_version = body.prompt_version
    await guide.save(update_fields=["prompt_version"])
    return {
        "success": True,
        "data": {"guide_id": str(guide.id), "prompt_version": guide.prompt_version},
        "message": "prompt_version 갱신 완료",
    }
