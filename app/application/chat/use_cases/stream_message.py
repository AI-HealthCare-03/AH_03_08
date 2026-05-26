from collections.abc import AsyncGenerator

from fastapi import HTTPException, status

from app.application.chat.dto.chat_dto import SendMessageCommand
from app.domain.chat.entity import ChatMessage
from app.domain.chat.llm_client import AbstractLLMClient
from app.domain.chat.repository import AbstractChatMessageRepository, AbstractChatSessionRepository

_CONTEXT_TURNS = 10
_MEDICAL_DISCLAIMER = "본 답변은 의료 전문가의 진단을 대체하지 않습니다. 정확한 진료는 반드시 의사와 상담하세요."
_MEDICAL_ONLY_GUARD = (
    "당신은 환자의 처방전을 기반으로 복약·건강 정보를 안내하는 AI 어시스턴트입니다. "
    "아래 처방전 정보를 참고하여 환자의 질문에 친절하고 구체적으로 답변하세요.\n"
    "규칙:\n"
    "1. 처방전·의약품·건강·복약 관련 질문이면 [처방전 정보]와 의학 지식을 함께 활용해 성실히 답변하세요.\n"
    "2. [처방전 정보]에 포함된 질병분류기호·약물명 등은 적극적으로 설명에 활용하세요. "
    "처방전에 없는 항목을 물어볼 때만 '처방전에 해당 정보가 포함되어 있지 않습니다. 담당 의사에게 문의해주세요.'라고 답하세요.\n"
    "3. 주식·날씨·게임 등 의료와 전혀 관계없는 질문에만 '죄송합니다. 저는 의료·건강 관련 질문만 답변할 수 있습니다.'라고 답하세요.\n"
    "4. 알러지 위험, 부작용, 금기사항, 약물 상호작용 등 환자 안전과 직결된 중요 주의사항을 포함할 때는 "
    "반드시 답변 맨 앞에 [경고]를 붙여 시작하세요. 이모지는 사용하지 마세요."
)


def _build_system_prompt(allergies: list[str], underlying_diseases: list[str], guide_context: str = "") -> str:
    parts = [_MEDICAL_ONLY_GUARD]
    if guide_context:
        parts.append(f"\n[처방전 정보]\n{guide_context}")
    if allergies:
        parts.append(f"[알러지] {', '.join(allergies)}")
    if underlying_diseases:
        parts.append(f"[기저질환] {', '.join(underlying_diseases)}")
    parts.append(_MEDICAL_DISCLAIMER)
    return "\n".join(parts)


class StreamMessageUseCase:
    def __init__(
        self,
        session_repo: AbstractChatSessionRepository,
        message_repo: AbstractChatMessageRepository,
        llm_client: AbstractLLMClient,
    ) -> None:
        self.session_repo = session_repo
        self.message_repo = message_repo
        self.llm_client = llm_client

    async def execute(self, command: SendMessageCommand) -> AsyncGenerator[str, None]:
        session = await self.session_repo.find_by_id(command.session_id, command.user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="채팅 세션을 찾을 수 없습니다.")

        await self.message_repo.save(ChatMessage(session_id=command.session_id, role="user", content=command.content))

        recent = await self.message_repo.find_recent_by_session_id(command.session_id, limit=_CONTEXT_TURNS)
        history = [{"role": m.role, "content": m.content} for m in reversed(recent)]
        system_prompt = _build_system_prompt(command.allergies, command.underlying_diseases, command.guide_context)

        return self._stream_and_save(command, history, system_prompt)

    async def _stream_and_save(
        self, command: SendMessageCommand, history: list[dict], system_prompt: str
    ) -> AsyncGenerator[str, None]:
        tokens: list[str] = []
        async for token in self.llm_client.stream(history, system_prompt):
            tokens.append(token)
            yield token

        full_reply = "".join(tokens)
        await self.message_repo.save(ChatMessage(session_id=command.session_id, role="assistant", content=full_reply))
