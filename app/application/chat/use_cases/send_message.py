
from fastapi import HTTPException, status

from app.application.chat.dto.chat_dto import SendMessageCommand
from app.domain.chat.entity import ChatMessage
from app.domain.chat.llm_client import AbstractLLMClient
from app.domain.chat.repository import AbstractChatMessageRepository, AbstractChatSessionRepository

_CONTEXT_TURNS = 10
_MEDICAL_DISCLAIMER = "본 답변은 의료 전문가의 진단을 대체하지 않습니다. 정확한 진료는 반드시 의사와 상담하세요."
_MEDICAL_ONLY_GUARD = (
    "당신은 헬스케어 전문 AI 어시스턴트입니다. "
    "의료·건강·복약과 관련 없는 질문에는 '죄송합니다. 저는 의료·건강 관련 질문만 답변할 수 있습니다.'라고만 답하세요."
)


def _build_system_prompt(
    allergies: list[str],
    underlying_diseases: list[str],
    medications: list[str],
) -> str:
    parts = [_MEDICAL_ONLY_GUARD]
    if allergies:
        parts.append(f"[알러지] {', '.join(allergies)}")
    if underlying_diseases:
        parts.append(f"[기저질환] {', '.join(underlying_diseases)}")
    if medications:
        parts.append(f"[복용 약물] {', '.join(medications)}")
    parts.append(_MEDICAL_DISCLAIMER)
    return "\n".join(parts)


class SendMessageUseCase:
    def __init__(
        self,
        session_repo: AbstractChatSessionRepository,
        message_repo: AbstractChatMessageRepository,
        llm_client: AbstractLLMClient,
    ) -> None:
        self.session_repo = session_repo
        self.message_repo = message_repo
        self.llm_client = llm_client

    async def execute(self, command: SendMessageCommand) -> ChatMessage:
        session = await self.session_repo.find_by_id(command.session_id, command.user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="채팅 세션을 찾을 수 없습니다.")

        user_message = await self.message_repo.save(
            ChatMessage(session_id=command.session_id, role="user", content=command.content)
        )

        recent = await self.message_repo.find_recent_by_session_id(command.session_id, limit=_CONTEXT_TURNS)
        # find_recent_by_session_id는 최신순으로 반환 → LLM에는 오래된 순으로 전달
        history = [{"role": m.role, "content": m.content} for m in reversed(recent)]

        system_prompt = _build_system_prompt(
            command.allergies,
            command.underlying_diseases,
            command.medications,
        )
        reply_text = await self.llm_client.complete(messages=history, system_prompt=system_prompt)

        assistant_message = await self.message_repo.save(
            ChatMessage(session_id=command.session_id, role="assistant", content=reply_text)
        )
        return assistant_message
