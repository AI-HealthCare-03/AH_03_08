from pydantic import BaseModel
from typing import Optional
from uuid import UUID


# =====================
# 요청 형식 (Request)
# =====================


class GuideGenerateRequest(BaseModel):
    """
    가이드 생성 요청 형식
    프론트에서 이 형식으로 보내줘야 해
    """

    record_id: str  # OCR 완료된 진료기록 ID


class FeedbackCreateRequest(BaseModel):
    """
    피드백 제출 요청 형식
    rating: 0(아쉬워요) or 1(도움됐어요)
    comment: 선택 입력
    """

    guide_id: str
    rating: int
    comment: Optional[str] = None  # 없어도 됨


# =====================
# 응답 형식 (Response)
# =====================


class GuideResponse(BaseModel):
    """
    가이드 조회 응답 형식
    """

    id: str
    record_id: str
    medication_guide: Optional[str] = None
    lifestyle_guide: Optional[str] = None
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = None
    created_at: Optional[str] = None


class FeedbackResponse(BaseModel):
    """
    피드백 조회 응답 형식
    """

    id: str
    guide_id: str
    rating: int
    comment: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
