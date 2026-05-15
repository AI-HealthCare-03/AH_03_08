from fastapi import APIRouter

router = APIRouter(prefix="/guides", tags=["guides"])


@router.get("")
async def get_guides():
    return {"success": True, "data": [], "message": "가이드 목록"}


@router.get("/{guide_id}")
async def get_guide(guide_id: str):
    return {"success": True, "data": {"guide_id": guide_id}, "message": "가이드 상세"}


@router.post("/generate", status_code=202)
async def generate_guide():
    return {"success": True, "data": {"guide_id": "test-123", "status": "processing"}, "message": "가이드 생성 요청"}