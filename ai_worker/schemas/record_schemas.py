from pydantic import BaseModel


class OcrTaskMessage(BaseModel):
    record_id: str
    file_path: str


class OcrTaskResult(BaseModel):
    record_id: str
    parsed_data: dict


class Medication(BaseModel):
    name: str
    dosage: float | None = None
    frequency: int | None = None
    days: int | None = None
    instructions: str | None = None


class ParsedRecord(BaseModel):
    patient_name: str | None = None
    issued_at: str | None = None
    hospital: str | None = None
    pharmacy: str | None = None
    doctor: str | None = None
    pharmacist: str | None = None
    medications: list[Medication] = []
