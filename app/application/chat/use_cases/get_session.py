from uuid import UUID

from fastapi import HTTPException, status

from app.domain.chat.entity import ChatSession
from app.domain.chat.repository import AbstractChatSessionRepository


class GetSessionUseCase:
    def __init__(self, repo: AbstractChatSessionRepository) -> None:
        self.repo = repo

    async def execute(self, session_id: UUID, user_id: int) -> ChatSession:
        session = await self.repo.find_by_id(session_id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="채팅 세션을 찾을 수 없습니다.")
        return session
