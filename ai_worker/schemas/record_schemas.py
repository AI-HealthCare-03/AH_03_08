from pydantic import BaseModel


class OcrTaskMessage(BaseModel):
    record_id: str
    file_path: str


class OcrTaskResult(BaseModel):
    record_id: str
    parsed_data: dict
