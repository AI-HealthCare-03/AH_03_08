from datetime import datetime

from app.core import config
from app.models.guides import Guide
from app.models.llm import (
    AssetType,
    ChatMessage,
    ChatSession,
    GuideAsset,
    GuideStatus,
    RecordStatus,
    RecordType,
)
from app.models.medical_records import MedicalRecord


class MedicalRecordRepository:
    def __init__(self):
        self._model = MedicalRecord

    async def create(self, user_id: int, record_type: RecordType, file_url: str | None = None) -> MedicalRecord:
        return await self._model.create(
            user_id=user_id,
            record_type=record_type,
            file_url=file_url,
        )

    async def get_by_id(self, record_id: int, user_id: int) -> MedicalRecord | None:
        return await self._model.get_or_none(id=record_id, user_id=user_id)

    async def get_completed_by_id(self, record_id, user_id: int) -> MedicalRecord | None:
        return await self._model.get_or_none(id=record_id, user_id=user_id, status="COMPLETED")

    async def get_list_by_user(self, user_id: int, page: int, limit: int) -> tuple[int, list[MedicalRecord]]:
        qs = self._model.filter(user_id=user_id).order_by("-created_at")
        total = await qs.count()
        items = await qs.offset((page - 1) * limit).limit(limit)
        return total, items

    async def update_parsed_data(self, record_id: int, parsed_data: dict) -> None:
        await self._model.filter(id=record_id).update(
            parsed_data=parsed_data,
            status=RecordStatus.DONE,
            updated_at=datetime.now(config.TIMEZONE),
        )


class GuideRepository:
    def __init__(self):
        self._model = Guide

    async def create(self, user_id: int, record_id) -> Guide:
        return await self._model.create(user_id=user_id, medical_record_id=record_id)

    async def get_by_id(self, guide_id: int, user_id: int) -> Guide | None:
        return await self._model.get_or_none(id=guide_id, user_id=user_id)

    async def get_list_by_user(self, user_id: int, page: int, limit: int) -> tuple[int, list[Guide]]:
        qs = self._model.filter(user_id=user_id).order_by("-created_at")
        total = await qs.count()
        items = await qs.offset((page - 1) * limit).limit(limit)
        return total, items

    async def update_done(
        self,
        guide_id: int,
        medication_guide: str,
        lifestyle_guide: str,
        summary: str,
        allergy_warnings: list,
        condition_interactions: list,
    ) -> None:
        await self._model.filter(id=guide_id).update(
            status=GuideStatus.DONE,
            medication_guide=medication_guide,
            lifestyle_guide=lifestyle_guide,
            summary=summary,
            allergy_warnings=allergy_warnings,
            condition_interactions=condition_interactions,
            completed_at=datetime.now(config.TIMEZONE),
            updated_at=datetime.now(config.TIMEZONE),
        )

    async def update_failed(self, guide_id: int) -> None:
        await self._model.filter(id=guide_id).update(
            status=GuideStatus.FAILED,
            updated_at=datetime.now(config.TIMEZONE),
        )


class GuideAssetRepository:
    def __init__(self):
        self._model = GuideAsset

    async def create(self, guide_id: int, asset_type: AssetType) -> GuideAsset:
        return await self._model.create(guide_id=guide_id, asset_type=asset_type)

    async def get_by_id(self, asset_id: int, guide_id: int) -> GuideAsset | None:
        return await self._model.get_or_none(id=asset_id, guide_id=guide_id)

    async def get_list_by_guide(self, guide_id: int) -> list[GuideAsset]:
        return await self._model.filter(guide_id=guide_id).order_by("created_at")

    async def update_done(self, asset_id: int, file_url: str) -> None:
        await self._model.filter(id=asset_id).update(
            status=RecordStatus.DONE,
            file_url=file_url,
            updated_at=datetime.now(config.TIMEZONE),
        )

    async def update_failed(self, asset_id: int) -> None:
        await self._model.filter(id=asset_id).update(
            status=RecordStatus.FAILED,
            updated_at=datetime.now(config.TIMEZONE),
        )


class ChatSessionRepository:
    def __init__(self):
        self._model = ChatSession

    async def create(self, user_id: int) -> ChatSession:
        return await self._model.create(user_id=user_id)

    async def get_by_id(self, session_id: int, user_id: int) -> ChatSession | None:
        return await self._model.get_or_none(id=session_id, user_id=user_id)

    async def get_list_by_user(self, user_id: int) -> list[ChatSession]:
        return await self._model.filter(user_id=user_id).order_by("-created_at").limit(50)

    async def delete(self, session_id: int) -> None:
        await self._model.filter(id=session_id).delete()


class ChatMessageRepository:
    def __init__(self):
        self._model = ChatMessage

    async def create(
        self,
        session_id: int,
        role: str,
        content: str = "",
        status: RecordStatus = RecordStatus.DONE,
    ) -> ChatMessage:
        return await self._model.create(
            session_id=session_id,
            role=role,
            content=content,
            status=status,
        )

    async def get_list_by_session(
        self,
        session_id: int,
        limit: int,
        cursor: int | None,
    ) -> list[ChatMessage]:
        qs = self._model.filter(session_id=session_id)
        if cursor:
            qs = qs.filter(id__gt=cursor)
        return await qs.order_by("created_at").limit(limit)

    async def update_content(self, message_id: int, content: str) -> None:
        await self._model.filter(id=message_id).update(
            content=content,
            status=RecordStatus.DONE,
        )
