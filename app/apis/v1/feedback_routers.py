from fastapi import APIRouter

router = APIRouter(prefix="/feedbacks", tags=["feedbacks"])


@router.post("")
async def create_feedback():
    return {
        "success": True,
        "data": {"feedback_id": "test-456"},
        "message": "피드백 제출 완료"
    }


@router.get("")
async def get_feedbacks():
    return {
        "success": True,
        "data": {"total": 0, "items": []},
        "message": "피드백 목록 조회 성공"
    }
