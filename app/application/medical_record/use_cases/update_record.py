from fastapi import HTTPException, status

from app.application.medical_record.dto.record_dto import UpdateRecordCommand
from app.domain.medical_record.entity import MedicalRecord
from app.domain.medical_record.repository import AbstractRecordRepository


class UpdateRecordUseCase:
    def __init__(self, repo: AbstractRecordRepository) -> None:
        self.repo = repo

    async def execute(self, command: UpdateRecordCommand) -> MedicalRecord:
        record = await self.repo.find_by_id(command.record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
        if record.user_id != command.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        return await self.repo.update_parsed_data(command.record_id, command.parsed_data)
