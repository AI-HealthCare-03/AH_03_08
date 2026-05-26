from fastapi import HTTPException, status

from app.repositories.guide_repository import (
    get_guide_by_id,
    get_guides_by_user,
)


def _guide_item(guide) -> dict:
    return {
        "id": str(guide.id),
        "record_id": str(guide.record_id),
        "title": guide.title,
        "status": guide.status,
        "medication_guide": guide.medication_guide,
        "lifestyle_guide": guide.lifestyle_guide,
        "summary_text": guide.summary_text,
        "allergy_warnings": guide.allergy_warnings,
        "condition_interactions": guide.condition_interactions,
        "llm_model": guide.llm_model,
        "llm_temperature": guide.llm_temperature,
        "created_at": guide.created_at.isoformat() if guide.created_at else None,
    }


async def list_my_guides(user_id: int) -> list[dict]:
    guides = await get_guides_by_user(user_id)
    return [_guide_item(g) for g in guides]


async def get_my_guide(guide_id: str, user_id: int) -> dict:
    guide = await get_guide_by_id(guide_id, user_id)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="가이드를 찾을 수 없습니다.")
    return _guide_item(guide)


async def get_my_guide_status(guide_id: str, user_id: int) -> dict:
    guide = await get_guide_by_id(guide_id, user_id)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="가이드를 찾을 수 없습니다.")
    return {"guide_id": str(guide.id), "status": guide.status}
