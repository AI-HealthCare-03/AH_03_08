from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.medical_record.value_objects import RecordStatus, RecordType


class UploadRecordRequestSchema(BaseModel):
    record_type: RecordType


class UpdateRecordRequestSchema(BaseModel):
    parsed_data: dict[str, Any]


class RecordResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: int
    record_type: RecordType
    status: RecordStatus
    ocr_raw_text: str | None = None
    parsed_data: dict[str, Any] | None = None
    created_at: datetime
    guide_id: UUID | None = None


class RecordListResponseSchema(BaseModel):
    total: int
    page: int
    items: list[RecordResponseSchema]
