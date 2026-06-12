from datetime import date, timedelta

from fastapi import HTTPException, status

from app.application.medical_record.dto.record_dto import UpdateRecordCommand
from app.domain.medical_record.entity import MedicalRecord
from app.domain.medical_record.repository import AbstractRecordRepository
from app.models.calendar_events import CalendarEvent
from app.models.medications import Medication
from app.models.notifications import Notification


class UpdateRecordUseCase:
    def __init__(self, repo: AbstractRecordRepository) -> None:
        self.repo = repo

    async def execute(self, command: UpdateRecordCommand) -> MedicalRecord:
        record = await self.repo.find_by_id(command.record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
        if record.user_id != command.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        updated = await self.repo.update_parsed_data(command.record_id, command.parsed_data)

        # medications 변경 시 캘린더/알림 재생성
        medications_data = command.parsed_data.get("medications")
        if medications_data is not None:
            await self._sync_medications(
                user_id=command.user_id,
                record_id=command.record_id,
                medications_data=medications_data,
            )

        return updated

    async def _sync_medications(self, user_id: int, record_id, medications_data: list) -> None:
        # 기존 데이터 삭제
        existing_meds = await Medication.filter(medical_record_id=record_id)
        med_ids = [m.id for m in existing_meds]
        if med_ids:
            await CalendarEvent.filter(medication_id__in=med_ids).delete()
            await Notification.filter(medication_id__in=med_ids).delete()
            await Medication.filter(medical_record_id=record_id).delete()

        # 새 데이터 생성
        for med_data in medications_data:
            med = await Medication.create(
                medical_record_id=record_id,
                drug_name=med_data.get("drug_name", ""),
                dosage=med_data.get("dosage"),
                frequency=med_data.get("frequency"),
                instructions=med_data.get("instructions"),
                warnings=med_data.get("warnings"),
                start_date=med_data.get("start_date"),
                end_date=med_data.get("end_date"),
                interval_days=med_data.get("interval_days"),
            )

            # 캘린더 자동생성
            start = med_data.get("start_date")
            end = med_data.get("end_date")
            interval = med_data.get("interval_days")
            if start and end and interval:
                if isinstance(start, str):
                    start = date.fromisoformat(start)
                if isinstance(end, str):
                    end = date.fromisoformat(end)
                events = []
                current = start
                while current <= end:
                    events.append(CalendarEvent(
                        user_id=user_id,
                        medication_id=med.id,
                        event_date=current,
                        scheduled_time="08:00:00",
                        status="PENDING",
                    ))
                    current += timedelta(days=interval)
                if events:
                    await CalendarEvent.bulk_create(events)

            # 알림 생성
            if med_data.get("start_date"):
                await Notification.create(
                    user_id=user_id,
                    medication_id=med.id,
                    title=f"{med.drug_name} 복용 알림",
                    type="push",
                    scheduled_time="08:00:00",
                    is_active=True,
                )