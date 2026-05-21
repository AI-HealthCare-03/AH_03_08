from pydantic import BaseModel

# =====================
# 요청 형식 (Request)
# =====================


class GuideGenerateRequest(BaseModel):
    """
    가이드 생성 요청 형식
    프론트에서 이 형식으로 보내줘야 해
    """

    medical_record_id: str  # 어떤 진료기록으로 가이드 만들지


class FeedbackCreateRequest(BaseModel):
    """
    피드백 제출 요청 형식
    rating: 0(아쉬워요) or 1(도움됐어요)
    comment: 선택 입력
    """

    guide_id: str
    rating: int
    comment: str | None = None  # 없어도 됨


# =====================
# 응답 형식 (Response)
# =====================


class GuideResponse(BaseModel):
    """
    가이드 조회 응답 형식
    """

    id: str
    medical_record_id: str
    medication_guide: str | None = None
    lifestyle_guide: str | None = None
    llm_model: str | None = None
    llm_temperature: float | None = None
    created_at: str | None = None


class FeedbackResponse(BaseModel):
    """
    피드백 조회 응답 형식
    """

    id: str
    guide_id: str
    rating: int
    comment: str | None = None
    status: str | None = None
    created_at: str | None = None
