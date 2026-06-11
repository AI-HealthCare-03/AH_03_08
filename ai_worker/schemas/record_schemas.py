from pydantic import BaseModel, Field


class OcrTaskMessage(BaseModel):
    record_id: str
    file_path: str


class OcrTaskResult(BaseModel):
    record_id: str
    parsed_data: dict


class Medication(BaseModel):
    name: str = Field(description="약품명. 용량(mg 등)은 제외하고 약품명만 (예: '모사피트정')")
    concentration: str | None = Field(default=None, description="약품 함량/농도 (예: '60mg', '0.2mg'). 약품명에 포함된 용량 정보")
    dosage: float | None = Field(default=None, description="1회 복용 정수(개수). 숫자만 (예: 1, 2, 0.5). '1정' → 1, '2캡슐' → 2. mg 농도가 아님")
    frequency: int | None = Field(default=None, description="1일 복용 횟수. 숫자만 (예: 3). '1일 3회' → 3, '하루 2번' → 2")
    days: int | None = Field(default=None, description="총 투약 일수 (숫자만, 예: 30)")
    instructions: str | None = Field(default=None, description="복용 지시사항 (예: '식후 30분')")
    drug_class: str | None = Field(default=None, description="약효분류명")


class ParsedRecord(BaseModel):
    patient_name: str | None = None
    issued_at: str | None = None
    hospital: str | None = None
    pharmacy: str | None = None
    doctor: str | None = None
    pharmacist: str | None = None
    disease_code: str | None = None
    disease_name: str | None = None
    medications: list[Medication] = []
