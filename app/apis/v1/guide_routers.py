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


@router.get("")
async def get_guides_api(current_user: User = Depends(get_request_user)):
    guides = await get_guides(user_id=str(current_user.id))
    return {"success": True, "data": {"total": len(guides), "items": [str(g.id) for g in guides]}, "message": "가이드 목록 조회 성공"}


@router.get("/feedbacks/list")
async def get_feedbacks_api(current_user: User = Depends(get_request_user)):
    feedbacks = await get_feedbacks()
    return {"success": True, "data": {"total": len(feedbacks), "items": [str(f.id) for f in feedbacks]}, "message": "피드백 목록 조회 성공"}


@router.get("/{guide_id}")
async def get_guide_api(guide_id: str, current_user: User = Depends(get_request_user)):
    guide = await get_guide(guide_id=guide_id, user_id=str(current_user.id))
    if not guide:
        raise HTTPException(status_code=404, detail="가이드를 찾을 수 없습니다.")
    return {"success": True, "data": {"id": str(guide.id), "medication_guide": guide.medication_guide, "lifestyle_guide": guide.lifestyle_guide, "llm_model": guide.llm_model, "created_at": str(guide.created_at)}, "message": "가이드 조회 성공"}


@router.post("/generate", status_code=202)
async def generate_guide_api(request: GuideGenerateRequest, current_user: User = Depends(get_request_user)):
    guide = await create_guide_service(user_id=str(current_user.id), medical_record_id=request.medical_record_id)
    from ai_worker.tasks.llm_task import generate_guide
    generate_guide.delay(
        guide_id=str(guide.id),
        medical_record_data={"medical_record_id": request.medical_record_id},
        user_info={"user_id": str(current_user.id)}
    )
    return {"success": True, "data": {"guide_id": str(guide.id), "status": "processing"}, "message": "가이드 생성 요청 완료"}


@router.post("/feedbacks")
async def create_feedback_api(request: FeedbackCreateRequest, current_user: User = Depends(get_request_user)):
    feedback = await create_feedback_service(user_id=str(current_user.id), guide_id=request.guide_id, rating=request.rating, comment=request.comment)
    return {"success": True, "data": {"feedback_id": str(feedback.id)}, "message": "피드백 제출 완료"}
