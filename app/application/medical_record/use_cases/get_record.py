from uuid import UUID

from fastapi import HTTPException, status

from app.domain.medical_record.entity import MedicalRecord
from app.domain.medical_record.repository import AbstractRecordRepository


class GetRecordUseCase:
    def __init__(self, repo: AbstractRecordRepository) -> None:
        self.repo = repo

    async def execute(self, record_id: UUID, user_id: int) -> MedicalRecord:
        record = await self.repo.find_by_id(record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
        if record.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        return record
