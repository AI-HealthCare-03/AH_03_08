from app.domain.medical_record.entity import MedicalRecord
from app.domain.medical_record.repository import AbstractRecordRepository


class ListRecordsUseCase:
    def __init__(self, repo: AbstractRecordRepository) -> None:
        self.repo = repo

    async def execute(self, user_id: int, page: int, limit: int) -> tuple[list[MedicalRecord], int]:
        return await self.repo.find_by_user_id_paginated(user_id, page, limit)
