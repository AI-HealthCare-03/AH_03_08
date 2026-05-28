from fastapi import HTTPException, status

from app.repositories.feedback_repository import (
    create_feedback,
    get_feedbacks_by_user,
)
from app.repositories.guide_repository import get_guide_by_id


async def submit_feedback(
    user_id: int,
    guide_id: str,
    rating: int,
    comment: str | None,
    tag_ids: list[str] | None = None,
) -> dict:
    guide = await get_guide_by_id(guide_id, user_id)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="가이드를 찾을 수 없습니다.")
    feedback = await create_feedback(
        user_id=user_id,
        guide_id=guide_id,
        rating=rating,
        comment=comment,
        tag_ids=tag_ids,
    )
    return {"feedback_id": str(feedback.id)}


async def list_my_feedbacks(user_id: int) -> list[dict]:
    rows = await get_feedbacks_by_user(user_id)
    return [
        {
            "id": str(f.id),
            "guide_id": str(f.guide_id),
            "rating": f.rating,
            "tag_ids": f.tag_ids or [],
            "comment": f.comment,
            "status": f.status,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in rows
    ]
