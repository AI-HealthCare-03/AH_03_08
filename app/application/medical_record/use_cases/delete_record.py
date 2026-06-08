from uuid import UUID

from fastapi import HTTPException, status

from app.domain.medical_record.repository import AbstractRecordRepository


class DeleteRecordUseCase:
    def __init__(self, repo: AbstractRecordRepository) -> None:
        self.repo = repo

    async def execute(self, record_id: UUID, user_id: int) -> None:
        record = await self.repo.find_by_id(record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
        if record.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        await self.repo.delete_by_id(record_id)
