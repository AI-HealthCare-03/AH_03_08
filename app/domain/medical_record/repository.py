from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.medical_record.entity import MedicalRecord


class AbstractRecordRepository(ABC):
    @abstractmethod
    async def save(self, record: MedicalRecord) -> MedicalRecord: ...

    @abstractmethod
    async def find_by_id(self, record_id: UUID) -> MedicalRecord | None: ...

    @abstractmethod
    async def find_by_user_id_paginated(
        self, user_id: int, page: int, limit: int
    ) -> tuple[list[MedicalRecord], int]: ...

    @abstractmethod
    async def update_parsed_data(self, record_id: UUID, parsed_data: dict) -> MedicalRecord: ...

    @abstractmethod
    async def delete_by_id(self, record_id: UUID) -> None: ...

    @abstractmethod
    async def delete_old_records(self, user_id: int, keep: int) -> None: ...
