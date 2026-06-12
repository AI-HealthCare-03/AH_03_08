from datetime import date

from fastapi import HTTPException, status

from app.models.model_metrics import MetricSnapshot
from app.repositories.feedback_repository import (
    create_feedback,
    get_feedbacks_by_user,
    get_feedbacks_paginated,
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
    # 피드백 제출 시 오늘 MetricSnapshot 업데이트
    await _update_metric_snapshot(model_type=guide.prompt_version or "unknown", rating=rating)
    return {"feedback_id": str(feedback.id)}


async def _update_metric_snapshot(model_type: str, rating: int) -> None:
    today = date.today()
    snapshot, created = await MetricSnapshot.get_or_create(
        model_type=model_type,
        snapshot_date=today,
        defaults={"avg_rating": rating, "total_count": 1},
    )
    if not created:
        # 누적 평균 업데이트
        new_total = snapshot.total_count + 1
        new_avg = ((snapshot.avg_rating or 0) * snapshot.total_count + rating) / new_total
        snapshot.avg_rating = round(new_avg, 4)
        snapshot.total_count = new_total
        await snapshot.save(update_fields=["avg_rating", "total_count"])


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


async def list_admin_feedbacks(page: int, limit: int) -> dict:
    rows, total = await get_feedbacks_paginated(page=page, limit=limit)
    items = [
        {
            "user_id": f.user_id,
            "guide_id": str(f.guide_id),
            "rating": f.rating,
            "comment": f.comment,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in rows
    ]
    return {"total": total, "page": page, "limit": limit, "items": items}
