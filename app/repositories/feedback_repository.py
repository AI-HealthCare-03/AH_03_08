from app.models.feedbacks import Feedback


async def create_feedback(
    user_id: int,
    guide_id: str,
    rating: int,
    comment: str | None = None,
    tag_ids: list[str] | None = None,
) -> Feedback:
    return await Feedback.create(
        user_id=user_id,
        guide_id=guide_id,
        rating=rating,
        tag_ids=tag_ids or [],
        comment=comment,
        status="ACTIVE",
    )


async def get_feedbacks_by_user(user_id: int) -> list[Feedback]:
    return await Feedback.filter(user_id=user_id).order_by("-created_at").all()
