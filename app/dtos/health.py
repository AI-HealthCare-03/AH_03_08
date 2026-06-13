from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel


class MedicalRecordCreateRequest(BaseModel):
    ocr_raw_text: str | None = None
    parsed_data: dict | None = None
    record_type: int = 0


class MedicalRecordResponse(BaseSerializerModel):
    id: UUID
    ocr_raw_text: str | None
    parsed_data: dict | None
    status: str
    record_type: int
    created_at: datetime


class MedicationCreateRequest(BaseModel):
    medical_record_id: str
    drug_name: str
    dosage: Annotated[str | None, Field(None, max_length=100)]
    frequency: Annotated[str | None, Field(None, max_length=100)]
    instructions: str | None = None
    warnings: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    interval_days: int | None = None


class MedicationResponse(BaseSerializerModel):
    id: UUID
    medical_record_id: UUID
    drug_name: str
    dosage: str | None
    frequency: str | None
    instructions: str | None
    warnings: str | None
    drug_class: str | None
    start_date: date | None
    end_date: date | None
    interval_days: int | None
    memo: str | None
    created_at: datetime


class UnderlyingDiseaseRequest(BaseModel):
    underlying_disease_name: str
    severity: str | None = None


class UnderlyingDiseaseResponse(BaseSerializerModel):
    id: UUID
    underlying_disease_name: str
    severity: str | None
    created_at: datetime


class AllergyRequest(BaseModel):
    allergy_name: str
    severity: str | None = None


class AllergyResponse(BaseSerializerModel):
    id: UUID
    allergy_name: str
    severity: str | None
    created_at: datetime


class DrugSearchItem(BaseModel):
    drug_name: str
    drug_class: str | None
    dosage: str | None


class AIAnalysisRequest(BaseModel):
    medical_record_id: str


class GuideResponse(BaseSerializerModel):
    id: UUID
    medical_record_id: UUID
    medication_guide: str | None
    lifestyle_guide: str | None
    llm_model: str | None
    created_at: datetime
