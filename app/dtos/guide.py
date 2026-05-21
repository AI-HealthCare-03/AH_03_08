from pydantic import BaseModel, Field


class GuideGenerateRequest(BaseModel):
    medical_record_id: str


class FeedbackCreateRequest(BaseModel):
    guide_id: str
    rating: int = Field(..., ge=0, le=1, description="0=아쉬워요, 1=도움됐어요")
    comment: str | None = None
