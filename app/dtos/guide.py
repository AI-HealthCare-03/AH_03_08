from typing import Optional

from pydantic import BaseModel


class GuideGenerateRequest(BaseModel):
    record_id: str


class FeedbackCreateRequest(BaseModel):
    guide_id: str
    rating: int
    comment: str | None = None


class GuideResponse(BaseModel):
    id: str
    record_id: str
    medication_guide: Optional[str] = None
    lifestyle_guide: Optional[str] = None
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = None
    created_at: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: str
    guide_id: str
    rating: int
    comment: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
