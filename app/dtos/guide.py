from pydantic import BaseModel, Field


class GuideGenerateRequest(BaseModel):
    """가이드 생성 요청 — 본인 진료기록 UUID만 허용."""

    record_id: str


class FeedbackCreateRequest(BaseModel):
    guide_id: str
    rating: int = Field(ge=0, le=1)  # 0: 부정, 1: 긍정 (ERD FEEDBACKS.rating)
    tag_ids: list[str] = Field(default_factory=list)  # FEEDBACK_TAGS uuid → FEEDBACK_TAG_SELECTIONS 저장 예정
    comment: str | None = None
