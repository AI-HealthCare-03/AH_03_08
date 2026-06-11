from datetime import date, timedelta

from fastapi import HTTPException
from starlette import status

from app.dtos.health import (
    AllergyRequest,
    MedicalRecordCreateRequest,
    MedicationCreateRequest,
    UnderlyingDiseaseRequest,
)
from app.models.calendar_events import CalendarEvent
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
        medication = await self.repo.create_medication(
            medical_record_id=data.medical_record_id,
            drug_name=data.drug_name,
            dosage=data.dosage,
            frequency=data.frequency,
            instructions=data.instructions,
            warnings=data.warnings,
            start_date=data.start_date,
            end_date=data.end_date,
            interval_days=data.interval_days,
        )
        # 캘린더 자동생성: start_date, end_date, interval_days 모두 있을 때
        if data.start_date and data.end_date and data.interval_days:
            await self._generate_calendar_events(
                user_id=user.id,
                medication_id=medication.id,
                start_date=data.start_date,
                end_date=data.end_date,
                interval_days=data.interval_days,
            )
        return medication

    async def _generate_calendar_events(
        self,
        user_id,
        medication_id,
        start_date: date,
        end_date: date,
        interval_days: int,
    ):
        current = start_date
        events = []
        while current <= end_date:
            events.append(
                CalendarEvent(
                    user_id=user_id,
                    medication_id=medication_id,
                    event_date=current,
                    scheduled_time="08:00:00",
                    status="PENDING",
                )
            )
            current += timedelta(days=interval_days)
        if events:
            await CalendarEvent.bulk_create(events)

    async def get_medications(self, user: User):
        return await self.repo.get_medications_by_user(user_id=user.id)

    async def create_disease(self, user: User, data: UnderlyingDiseaseRequest):
        return await self.repo.create_disease(
            user_id=user.id, name=data.underlying_disease_name, severity=data.severity
        )

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