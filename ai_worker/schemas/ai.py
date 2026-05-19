from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    user_id: int
    record_id: str
    data: dict


class AnalysisResult(BaseModel):
    user_id: int
    record_id: str
    status: str
    result: dict | None
    error: str | None
