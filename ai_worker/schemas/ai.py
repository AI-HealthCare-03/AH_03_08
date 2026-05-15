from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    user_id: int
    record_id: int
    data: dict


class AnalysisResult(BaseModel):
    user_id: int
    record_id: int
    status: str
    result: dict | None
    error: str | None