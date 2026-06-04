from app.domain.chat.entity import ChatMessage, ChatSession
from app.domain.chat.repository import AbstractChatMessageRepository, AbstractChatSessionRepository
from app.models.chat_messages import ChatMessage as ChatMessageORM
from app.models.chat_sessions import ChatSession as ChatSessionORM


class TortoiseChatSessionRepository(AbstractChatSessionRepository):
    def _to_domain(self, orm: ChatSessionORM) -> ChatSession:
        return ChatSession(
            id=orm.id,
            user_id=orm.user_id,
            guide_id=orm.guide_id,
            title=orm.title,
            created_at=orm.created_at,
            last_active_at=orm.last_active_at,
        )

    async def save(self, session: ChatSession) -> ChatSession:
        orm = await ChatSessionORM.create(
            user_id=session.user_id,
            guide_id=session.guide_id,
            title=session.title,
        )
        return self._to_domain(orm)

    async def find_by_id(self, session_id: int, user_id: int) -> ChatSession | None:
        orm = await ChatSessionORM.get_or_none(id=session_id, user_id=user_id)
        return self._to_domain(orm) if orm else None

    async def find_by_user_id_paginated(self, user_id: int, page: int, limit: int) -> tuple[list[ChatSession], int]:
        qs = ChatSessionORM.filter(user_id=user_id).order_by("-last_active_at")
        total = await qs.count()
        sessions = await qs.offset((page - 1) * limit).limit(limit)
        return [self._to_domain(s) for s in sessions], total

    async def delete(self, session_id: int, user_id: int) -> bool:
        deleted = await ChatSessionORM.filter(id=session_id, user_id=user_id).delete()
        return deleted > 0


class TortoiseChatMessageRepository(AbstractChatMessageRepository):
    def _to_domain(self, orm: ChatMessageORM) -> ChatMessage:
        return ChatMessage(
            id=orm.id,
            session_id=orm.session_id,
            role=orm.role,
            content=orm.content,
            created_at=orm.created_at,
        )

    async def save(self, message: ChatMessage) -> ChatMessage:
        orm = await ChatMessageORM.create(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
        )
        return self._to_domain(orm)

    async def find_recent_by_session_id(self, session_id: int, limit: int) -> list[ChatMessage]:
        rows = await ChatMessageORM.filter(session_id=session_id).order_by("-created_at").limit(limit)
        return [self._to_domain(r) for r in rows]