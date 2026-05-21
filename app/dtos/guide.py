from pydantic import BaseModel, Field


class GuideGenerateRequest(BaseModel):
    """가이드 생성 요청 — 본인 진료기록 UUID만 허용."""

    record_id: str


class FeedbackCreateRequest(BaseModel):
    guide_id: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = None
