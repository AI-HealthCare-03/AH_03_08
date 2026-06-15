from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.celery_client import celery_client as celery_app
from app.dependencies.security import get_request_user
from app.dtos.guide import FeedbackCreateRequest, GuideGenerateRequest
from app.models.medical_records import MedicalRecord
from app.models.users import User
from app.repositories.guide_repository import create_guide
from app.services import feedback_service
from app.services import guide as guide_service

from datetime import UTC, datetime
from app.models.guide import Guide as GuideModel

GENERATE_GUIDE_TASK = "ai_worker.tasks.llm_task.generate_guide_task"

guide_router = APIRouter(prefix="/guides", tags=["guides"])
CurrentUser = Annotated[User, Depends(get_request_user)]


def _ok(data, message: str) -> dict:
    return {"success": True, "data": data, "message": message}


@guide_router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_guide_api(request: GuideGenerateRequest, current_user: CurrentUser):
    # 개인정보: 본인 소유 진료기록만 가이드 생성 가능
    record = await MedicalRecord.get_or_none(id=request.record_id, user_id=current_user.id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료기록을 찾을 수 없습니다.")

    from app.models.guide import Guide

    existing = await Guide.get_or_none(record_id=request.record_id, user_id=current_user.id)
    if existing:
        return _ok({"guide_id": str(existing.id), "status": existing.status}, "가이드 생성 요청 완료")

    guide = await create_guide(user_id=current_user.id, record_id=request.record_id)
    celery_app.send_task(
        GENERATE_GUIDE_TASK,
        kwargs={
            "guide_id": str(guide.id),
            "record_id": str(request.record_id),
            "user_id": current_user.id,
        },
        queue="llm",
    )
    return _ok({"guide_id": str(guide.id), "status": guide.status}, "가이드 생성 요청 완료")


@guide_router.get("/feedbacks/list")
async def list_feedbacks_api(current_user: CurrentUser):
    items = await feedback_service.list_my_feedbacks(user_id=current_user.id)
    return _ok({"total": len(items), "items": items}, "피드백 목록 조회 성공")


@guide_router.post("/feedbacks")
async def create_feedback_api(request: FeedbackCreateRequest, current_user: CurrentUser):
    data = await feedback_service.submit_feedback(
        user_id=current_user.id,
        guide_id=request.guide_id,
        rating=request.rating,
        comment=request.comment,
        tag_ids=request.tag_ids,
    )
    return _ok(data, "피드백 제출 완료")


@guide_router.get("")
async def list_guides_api(current_user: CurrentUser):
    items = await guide_service.list_my_guides(user_id=current_user.id)
    return _ok({"total": len(items), "items": items}, "가이드 목록 조회 성공")


@guide_router.get("/{guide_id}/status")
async def get_guide_status_api(guide_id: str, current_user: CurrentUser):
    data = await guide_service.get_my_guide_status(guide_id=guide_id, user_id=current_user.id)
    return _ok(data, "가이드 상태 조회 성공")


@guide_router.get("/{guide_id}")
async def get_guide_api(guide_id: str, current_user: CurrentUser):
    data = await guide_service.get_my_guide(guide_id=guide_id, user_id=current_user.id)
    guide_obj = await GuideModel.get_or_none(id=guide_id, user_id=current_user.id)
    if guide_obj and not guide_obj.is_read:
        guide_obj.is_read = True
        guide_obj.read_at = datetime.now(UTC)
        await guide_obj.save(update_fields=["is_read", "read_at"])
    
    return _ok(data, "가이드 조회 성공")
