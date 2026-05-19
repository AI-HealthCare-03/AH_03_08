from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.domain.medical_record.value_objects import RecordType


@dataclass
class UploadRecordCommand:
    user_id: int
    record_type: RecordType
    file_content: bytes
    original_filename: str


@dataclass
class UpdateRecordCommand:
    record_id: UUID
    user_id: int
    parsed_data: dict[str, Any]
