from app.domain.chat.entity import ChatSession
from app.domain.chat.repository import AbstractChatSessionRepository


class ListSessionsUseCase:
    def __init__(self, repo: AbstractChatSessionRepository) -> None:
        self.repo = repo

    async def execute(self, user_id: int, page: int, limit: int) -> tuple[list[ChatSession], int]:
        return await self.repo.find_by_user_id_paginated(user_id=user_id, page=page, limit=limit)
