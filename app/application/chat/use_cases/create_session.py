from app.application.chat.dto.chat_dto import CreateSessionCommand
from app.domain.chat.entity import ChatSession
from app.domain.chat.repository import AbstractChatSessionRepository


class CreateSessionUseCase:
    def __init__(self, repo: AbstractChatSessionRepository) -> None:
        self.repo = repo

    async def execute(self, command: CreateSessionCommand) -> ChatSession:
        session = ChatSession(
            user_id=command.user_id,
            guide_id=command.guide_id,
            title=command.title,
        )
        return await self.repo.save(session)
