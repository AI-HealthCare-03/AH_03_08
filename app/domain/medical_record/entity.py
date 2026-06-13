from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.domain.medical_record.value_objects import RecordStatus, RecordType


@dataclass
class MedicalRecord:
    user_id: int
    record_type: RecordType
    id: UUID = field(default_factory=uuid4)
    status: RecordStatus = RecordStatus.PENDING
    ocr_raw_text: str | None = None
    parsed_data: dict[str, Any] | None = None
    file_url: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    guide_id: UUID | None = None
