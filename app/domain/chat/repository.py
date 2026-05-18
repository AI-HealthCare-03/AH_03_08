from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.chat.entity import ChatMessage, ChatSession


class AbstractChatSessionRepository(ABC):
    @abstractmethod
    async def save(self, session: ChatSession) -> ChatSession: ...

    @abstractmethod
    async def find_by_id(self, session_id: UUID, user_id: int) -> ChatSession | None: ...

    @abstractmethod
    async def find_by_user_id_paginated(
        self, user_id: int, page: int, limit: int
    ) -> tuple[list[ChatSession], int]: ...

    @abstractmethod
    async def delete(self, session_id: UUID, user_id: int) -> bool: ...


class AbstractChatMessageRepository(ABC):
    @abstractmethod
    async def save(self, message: ChatMessage) -> ChatMessage: ...

    @abstractmethod
    async def find_recent_by_session_id(self, session_id: UUID, limit: int) -> list[ChatMessage]: ...
