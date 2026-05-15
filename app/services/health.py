from fastapi import HTTPException
from starlette import status

from app.dtos.health import (
    MedicalRecordCreateRequest, MedicationCreateRequest,
    UnderlyingDiseaseRequest, AllergyRequest,
)
from app.models.users import User
from app.repositories.health_repository import HealthRepository


class HealthService:
    def __init__(self):
        self.repo = HealthRepository()

    async def create_record(self, user: User, data: MedicalRecordCreateRequest):
        return await self.repo.create_record(
            user_id=user.id,
            ocr_raw_text=data.ocr_raw_text,
            parsed_data=data.parsed_data,
            record_type=data.record_type,
        )

    async def get_record_or_404(self, record_id: str, user: User):
        record = await self.repo.get_record(record_id=record_id, user_id=user.id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="의료기록을 찾을 수 없습니다.")
        return record

    async def get_records(self, user: User, limit: int = 20, offset: int = 0):
        return await self.repo.get_records_by_user(user_id=user.id, limit=limit, offset=offset)

    async def create_medication(self, user: User, data: MedicationCreateRequest):
        await self.get_record_or_404(record_id=data.medical_record_id, user=user)
        return await self.repo.create_medication(
            medical_record_id=data.medical_record_id,
            drug_name=data.drug_name,
            dosage=data.dosage,
            frequency=data.frequency,
            instructions=data.instructions,
            warnings=data.warnings,
        )

    async def create_disease(self, user: User, data: UnderlyingDiseaseRequest):
        return await self.repo.create_disease(user_id=user.id, name=data.underlying_disease_name, severity=data.severity)

    async def get_diseases(self, user: User):
        return await self.repo.get_diseases_by_user(user_id=user.id)

    async def delete_disease(self, disease_id: str, user: User):
        deleted = await self.repo.delete_disease(disease_id=disease_id, user_id=user.id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="기저질환을 찾을 수 없습니다.")

    async def create_allergy(self, user: User, data: AllergyRequest):
        return await self.repo.create_allergy(user_id=user.id, name=data.allergy_name, severity=data.severity)

    async def get_allergies(self, user: User):
        return await self.repo.get_allergies_by_user(user_id=user.id)

    async def delete_allergy(self, allergy_id: str, user: User):
        deleted = await self.repo.delete_allergy(allergy_id=allergy_id, user_id=user.id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="알러지를 찾을 수 없습니다.")