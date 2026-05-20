from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.security import get_request_user
from app.dtos.guide import FeedbackCreateRequest, GuideGenerateRequest
from app.models.users import User
from app.services.guide import (
    create_feedback_service,
    create_guide_service,
    get_feedbacks,
    get_guide,
    get_guides,
)

router = APIRouter(prefix="/guides", tags=["guides"])

CurrentUser = Annotated[User, Depends(get_request_user)]


@router.get("")
async def get_guides_api(current_user: CurrentUser):
    guides = await get_guides(user_id=current_user.id)
    return {
        "success": True,
        "data": {"total": len(guides), "items": [str(g.id) for g in guides]},
        "message": "가이드 목록 조회 성공",
    }


@router.get("/feedbacks/list")
async def get_feedbacks_api(current_user: CurrentUser):
    feedbacks = await get_feedbacks()
    return {
        "success": True,
        "data": {"total": len(feedbacks), "items": [str(f.id) for f in feedbacks]},
        "message": "피드백 목록 조회 성공",
    }


@router.get("/{guide_id}/status")
async def get_guide_status_api(guide_id: str, current_user: CurrentUser):
    """가이드 생성 진행 여부를 폴링할 때 사용 (processing → done / failed)."""
    guide = await get_guide(guide_id=guide_id, user_id=current_user.id)
    if not guide:
        raise HTTPException(status_code=404, detail="가이드를 찾을 수 없습니다.")
    return {
        "success": True,
        "data": {"guide_id": str(guide.id), "status": guide.status},
        "message": "가이드 상태 조회 성공",
    }


@router.get("/{guide_id}")
async def get_guide_api(guide_id: str, current_user: CurrentUser):
    guide = await get_guide(guide_id=guide_id, user_id=current_user.id)
    if not guide:
        raise HTTPException(status_code=404, detail="가이드를 찾을 수 없습니다.")
    return {
        "success": True,
        "data": {
            "id": str(guide.id),
            "status": guide.status,
            "medication_guide": guide.medication_guide,
            "lifestyle_guide": guide.lifestyle_guide,
            "summary_text": guide.summary_text,
            "llm_model": guide.llm_model,
            "created_at": str(guide.created_at),
        },
        "message": "가이드 조회 성공",
    }


@router.post("/generate", status_code=202)
async def generate_guide_api(request: GuideGenerateRequest, current_user: CurrentUser):
    guide = await create_guide_service(
        user_id=current_user.id,
        medical_record_id=request.medical_record_id,
    )
    from ai_worker.tasks.llm_tasks import generate_guide_task

    generate_guide_task.apply_async(
        kwargs={
            "guide_id": str(guide.id),
            "record_id": request.medical_record_id,
            "user_id": current_user.id,
        },
        queue="llm",
    )
    return {
        "success": True,
        "data": {"guide_id": str(guide.id), "status": "processing"},
        "message": "가이드 생성 요청 완료",
    }


@router.post("/feedbacks")
async def create_feedback_api(request: FeedbackCreateRequest, current_user: CurrentUser):
    feedback = await create_feedback_service(
        user_id=current_user.id,
        guide_id=request.guide_id,
        rating=request.rating,
        comment=request.comment,
    )
    return {"success": True, "data": {"feedback_id": str(feedback.id)}, "message": "피드백 제출 완료"}
