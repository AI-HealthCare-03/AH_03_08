from fastapi import HTTPException, status

from app.repositories.guide_repository import (
    create_feedback,
    get_feedbacks_by_user,
    get_guide_by_id,
    get_guides_by_user,
)


def _guide_item(guide) -> dict:
    return {
        "id": str(guide.id),
        "record_id": str(guide.record_id),
        "status": guide.status,
        "medication_guide": guide.medication_guide,
        "lifestyle_guide": guide.lifestyle_guide,
        "summary_text": guide.summary_text,
        "llm_model": guide.llm_model,
        "llm_temperature": guide.llm_temperature,
        "prompt_version": guide.prompt_version,
        "created_at": guide.created_at.isoformat() if guide.created_at else None,
    }


async def list_my_guides(user_id: int) -> list[dict]:
    return [_guide_item(g) for g in await get_guides_by_user(user_id)]


async def get_my_guide(guide_id: str, user_id: int) -> dict:
    guide = await get_guide_by_id(guide_id, user_id)
    if not guide:
        raise HTTPException(status_code=404, detail="가이드를 찾을 수 없습니다.")
    return _guide_item(guide)


async def get_my_guide_status(guide_id: str, user_id: int) -> dict:
    guide = await get_guide_by_id(guide_id, user_id)
    if not guide:
        raise HTTPException(status_code=404, detail="가이드를 찾을 수 없습니다.")
    return {"guide_id": str(guide.id), "status": guide.status}


async def submit_feedback(user_id: int, guide_id: str, rating: int, comment: str | None) -> dict:
    guide = await get_guide_by_id(guide_id, user_id)
    if not guide:
        raise HTTPException(status_code=404, detail="가이드를 찾을 수 없습니다.")
    feedback = await create_feedback(user_id=user_id, guide_id=guide_id, rating=rating, comment=comment)
    return {"feedback_id": str(feedback.id)}


async def list_my_feedbacks(user_id: int) -> list[dict]:
    rows = await get_feedbacks_by_user(user_id)
    return [
        {
            "id": str(f.id),
            "guide_id": str(f.guide_id),
            "rating": f.rating,
            "comment": f.comment,
            "status": f.status,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in rows
    ]
