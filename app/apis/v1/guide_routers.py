from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.guide import (
    get_guides,
    get_guide,
    create_guide,
    create_feedback,
    get_feedbacks
)

router = APIRouter(prefix="/guides", tags=["guides"])


# 요청 데이터 형식 정의
class GuideGenerateRequest(BaseModel):
    medical_record_id: str  # 어떤 진료기록으로 가이드 만들지


class FeedbackCreateRequest(BaseModel):
    guide_id: str
    rating: int        # 평점
    comment: str = None  # 선택 입력


# 가이드 목록 조회
@router.get("")
async def get_guides_api(user_id: str):
    # 개인정보 보호: 본인 가이드만 조회 가능
    guides = await get_guides(user_id=user_id)
    return {
        "success": True,
        "data": {"total": len(guides), "items": [str(g.id) for g in guides]},
        "message": "가이드 목록 조회 성공"
    }


# 가이드 상세 조회
@router.get("/{guide_id}")
async def get_guide_api(guide_id: str, user_id: str):
    guide = await get_guide(guide_id=guide_id, user_id=user_id)
    if not guide:
        raise HTTPException(status_code=404, detail="가이드를 찾을 수 없습니다.")
    return {
        "success": True,
        "data": {
            "id": str(guide.id),
            "medication_guide": guide.medication_guide,
            "lifestyle_guide": guide.lifestyle_guide,
            "llm_model": guide.llm_model,
            "created_at": str(guide.created_at)
        },
        "message": "가이드 조회 성공"
    }


# 가이드 생성 요청
@router.post("/generate", status_code=202)
async def generate_guide_api(request: GuideGenerateRequest, user_id: str):
    guide = await create_guide(
        user_id=user_id,
        medical_record_id=request.medical_record_id
    )
    return {
        "success": True,
        "data": {"guide_id": str(guide.id), "status": "processing"},
        "message": "가이드 생성 요청 완료"
    }


# 피드백 제출
@router.post("/feedbacks")
async def create_feedback_api(request: FeedbackCreateRequest, user_id: str):
    feedback = await create_feedback(
        user_id=user_id,
        guide_id=request.guide_id,
        rating=request.rating,
        comment=request.comment
    )
    return {
        "success": True,
        "data": {"feedback_id": str(feedback.id)},
        "message": "피드백 제출 완료"
    }


# 피드백 목록 조회 (관리자용)
@router.get("/feedbacks/list")
async def get_feedbacks_api():
    feedbacks = await get_feedbacks()
    return {
        "success": True,
        "data": {"total": len(feedbacks), "items": [str(f.id) for f in feedbacks]},
        "message": "피드백 목록 조회 성공"
    }