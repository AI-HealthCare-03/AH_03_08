from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.security import get_request_user
from app.dtos.guide import FeedbackCreateRequest
from app.models.users import User
from app.services import feedback_service

feedback_router = APIRouter(prefix="/feedbacks", tags=["feedbacks"])
CurrentUser = Annotated[User, Depends(get_request_user)]


def _ok(data, message: str) -> dict:
    return {"success": True, "data": data, "message": message}


@feedback_router.post("")
async def create_feedback_api(request: FeedbackCreateRequest, current_user: CurrentUser):
    data = await feedback_service.submit_feedback(
        user_id=current_user.id,
        guide_id=request.guide_id,
        rating=request.rating,
        comment=request.comment,
    )
    return _ok(data, "피드백 제출 완료")


@feedback_router.get("")
async def get_feedbacks(current_user: CurrentUser):
    items = await feedback_service.list_my_feedbacks(user_id=current_user.id)
    return _ok({"total": len(items), "items": items}, "피드백 목록 조회 성공")
