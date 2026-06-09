from fastapi.exceptions import HTTPException
from starlette import status
from tortoise.transactions import in_transaction

from app.core.celery_client import celery_client as celery_app
from app.models.llm import AssetType, GuideStatus, RecordStatus, RecordType
from app.repositories.llm_repository import (
    ChatMessageRepository,
    ChatSessionRepository,
    GuideAssetRepository,
    GuideRepository,
    MedicalRecordRepository,
)

# ════════════════════════════════════════
# MedicalRecordService
# ════════════════════════════════════════


class MedicalRecordService:
    def __init__(self):
        self.repo = MedicalRecordRepository()

    async def create_record(self, user_id: int, record_type: RecordType, file_url: str) -> dict:
        record = await self.repo.create(
            user_id=user_id,
            record_type=record_type,
            file_url=file_url,
        )
        return record

    async def get_record(self, record_id: str, user_id: int):
        record = await self.repo.get_by_id(record_id, user_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="레코드를 찾을 수 없습니다.",
            )
        return record

    async def get_record_list(self, user_id: int, page: int, limit: int) -> tuple:
        return await self.repo.get_list_by_user(user_id, page, limit)


# ════════════════════════════════════════
# GuideService
# ════════════════════════════════════════


class GuideService:
    def __init__(self):
        self.guide_repo = GuideRepository()
        self.record_repo = MedicalRecordRepository()
        self.asset_repo = GuideAssetRepository()

    async def generate_guide(self, user_id: int, record_id: str):
        # OCR 완료된 레코드인지 확인
        record = await self.record_repo.get_completed_by_id(record_id, user_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OCR 처리가 완료되지 않았거나 존재하지 않는 레코드입니다.",
            )

        # [수정 9] 동일 record에 처리 중이거나 완료된 가이드가 있으면 재생성 차단
        # 기존: get_list_by_user() 결과를 unused variable로 받고 아무 처리도 안 함
        existing = await self.guide_repo.get_active_by_record(record_id, user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"이미 {'처리 중인' if existing.status == 'processing' else '완료된'} 가이드가 있습니다. (guide_id: {existing.id})",
            )

        # Guide 생성 (status=processing)
        async with in_transaction():
            guide = await self.guide_repo.create(user_id=user_id, record_id=record_id)

        # Celery Task 발행 — LLM Worker가 백그라운드에서 처리
        celery_app.send_task(
            "ai_worker.tasks.llm_task.generate_guide_task",
            kwargs={"guide_id": str(guide.id), "record_id": str(record_id), "user_id": user_id},
            queue="llm",
        )

        return guide

    async def get_guide(self, guide_id: int, user_id: int):
        guide = await self.guide_repo.get_by_id(guide_id, user_id)
        if not guide:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="가이드를 찾을 수 없습니다.",
            )
        return guide

    async def get_guide_list(self, user_id: int, page: int, limit: int) -> tuple:
        return await self.guide_repo.get_list_by_user(user_id, page, limit)

    async def create_asset(self, guide_id: int, user_id: int, asset_type: AssetType):
        # 가이드 존재 + 소유권 확인
        guide = await self.get_guide(guide_id, user_id)

        # 가이드가 완료된 상태여야 에셋 생성 가능
        if guide.status != GuideStatus.DONE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="가이드 생성이 완료된 후 에셋을 생성할 수 있습니다.",
            )

        asset = await self.asset_repo.create(guide_id=guide_id, asset_type=asset_type)

        celery_app.send_task(
            "ai_worker.tasks.image_task.generate_card_image_task",
            kwargs={"asset_id": str(asset.id), "guide_id": str(guide_id)},
            queue="image",
        )

        return asset

    async def get_asset(self, guide_id: int, asset_id: int, user_id: int):
        # 가이드 소유권 먼저 확인
        await self.get_guide(guide_id, user_id)

        asset = await self.asset_repo.get_by_id(asset_id, guide_id)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="에셋을 찾을 수 없습니다.",
            )
        return asset

    async def get_asset_list(self, guide_id: int, user_id: int):
        # 가이드 소유권 먼저 확인
        await self.get_guide(guide_id, user_id)
        return await self.asset_repo.get_list_by_guide(guide_id)


# ════════════════════════════════════════
# ChatService
# ════════════════════════════════════════


class ChatService:
    def __init__(self):
        self.session_repo = ChatSessionRepository()
        self.message_repo = ChatMessageRepository()

    async def create_session(self, user_id: int):
        session = await self.session_repo.create(user_id=user_id)
        return session

    async def get_session_list(self, user_id: int):
        return await self.session_repo.get_list_by_user(user_id)

    async def delete_session(self, session_id: int, user_id: int) -> None:
        # 소유권 확인
        session = await self.session_repo.get_by_id(session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없습니다.",
            )
        await self.session_repo.delete(session_id)

    async def get_message_list(self, session_id: int, user_id: int, limit: int, cursor: int | None):
        # 소유권 확인
        session = await self.session_repo.get_by_id(session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없습니다.",
            )
        return await self.message_repo.get_list_by_session(session_id, limit, cursor)

    async def send_message(self, session_id: int, user_id: int, message: str):
        # 소유권 확인
        session = await self.session_repo.get_by_id(session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없습니다.",
            )

        async with in_transaction():
            # 사용자 메시지 저장
            await self.message_repo.create(
                session_id=session_id,
                role="user",
                content=message,
                status=RecordStatus.DONE,
            )

            # 어시스턴트 메시지 placeholder 저장 (LLM이 채워줌)
            assistant_msg = await self.message_repo.create(
                session_id=session_id,
                role="assistant",
                content="",
                status=RecordStatus.PROCESSING,
            )

        # Celery Task 발행 — LLM Worker가 스트리밍 응답 처리
        celery_app.send_task(
            "ai_worker.tasks.llm_task.process_chat_message_task",
            kwargs={
                "session_id": session_id,
                "message_id": assistant_msg.id,
                "user_id": user_id,
                "user_message": message,
            },
            queue="llm",
        )

        return assistant_msg
