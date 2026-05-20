from app.repositories.guide_repository import (
    create_feedback,
    create_guide,
    get_all_feedbacks,
    get_guide_by_id,
    get_guides_by_user,
)


async def get_guides(user_id: int):
    return await get_guides_by_user(user_id=user_id)


async def get_guide(guide_id: str, user_id: int):
    return await get_guide_by_id(guide_id=guide_id, user_id=user_id)


async def create_guide_service(user_id: int, medical_record_id: str):
    return await create_guide(user_id=user_id, medical_record_id=medical_record_id)


async def create_feedback_service(user_id: int, guide_id: str, rating: int, comment: str = None):
    return await create_feedback(user_id=user_id, guide_id=guide_id, rating=rating, comment=comment)


async def get_feedbacks():
    return await get_all_feedbacks()
