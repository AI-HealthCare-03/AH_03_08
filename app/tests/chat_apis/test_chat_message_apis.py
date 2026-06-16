import uuid
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.application.chat.dto.chat_dto import SendMessageCommand
from app.application.chat.use_cases.stream_message import StreamMessageUseCase
from app.infrastructure.chat.llm_client import StubLLMClient
from app.infrastructure.chat.repository import TortoiseChatMessageRepository, TortoiseChatSessionRepository
from app.main import app
from app.models.users import User

_SIGNUP = {
    "email": "msg_test@example.com",
    "email_token": "msg_test@example.com",
    "password": "Password123!",
    "name": "메시지테스터",
    "gender": "MALE",
    "birth_date": "1990-01-01",
    "phone_number": "01099990000",
}
_LOGIN = {"email": "msg_test@example.com", "password": "Password123!"}


async def _get_auth_headers(client: AsyncClient) -> dict:
    await client.post("/api/v1/auth/signup", json=_SIGNUP)
    resp = await client.post("/api/v1/auth/login", json=_LOGIN)
    return {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}


async def _create_session(client: AsyncClient, headers: dict) -> str:
    resp = await client.post("/api/v1/chats", headers=headers, json={})
    return resp.json()["id"]


async def _get_user(client: AsyncClient) -> User:
    await client.post("/api/v1/auth/signup", json=_SIGNUP)
    return await User.get(email=_SIGNUP["email"])


class TestStreamMessageUseCase(TestCase):
    """StreamMessageUseCase를 직접 테스트 — WebSocket 레이어 없이 비즈니스 로직만 검증."""

    async def test_streams_tokens(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            session_id = await _create_session(client, headers)
            user = await User.get(email=_SIGNUP["email"])

        session_repo = TortoiseChatSessionRepository()
        message_repo = TortoiseChatMessageRepository()
        use_case = StreamMessageUseCase(session_repo, message_repo, StubLLMClient())

        command = SendMessageCommand(
            session_id=uuid.UUID(session_id),
            user_id=user.id,
            content="아스피린 주의사항 알려주세요",
        )

        tokens = []
        generator = await use_case.execute(command)
        async for token in generator:
            tokens.append(token)

        assert len(tokens) > 0
        full_reply = "".join(tokens)
        assert len(full_reply) > 0

    async def test_saves_user_and_assistant_messages(self):
        from app.models.chat_messages import ChatMessage as ChatMessageORM

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            session_id = await _create_session(client, headers)
            user = await User.get(email=_SIGNUP["email"])

        session_repo = TortoiseChatSessionRepository()
        message_repo = TortoiseChatMessageRepository()
        use_case = StreamMessageUseCase(session_repo, message_repo, StubLLMClient())

        command = SendMessageCommand(
            session_id=uuid.UUID(session_id),
            user_id=user.id,
            content="복약 질문입니다.",
        )
        generator = await use_case.execute(command)
        async for _ in generator:
            pass

        messages = await ChatMessageORM.filter(session_id=session_id).order_by("created_at")
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "복약 질문입니다."
        assert messages[1].role == "assistant"

    async def test_session_not_found_raises_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await _get_auth_headers(client)
            user = await User.get(email=_SIGNUP["email"])

        session_repo = TortoiseChatSessionRepository()
        message_repo = TortoiseChatMessageRepository()
        use_case = StreamMessageUseCase(session_repo, message_repo, StubLLMClient())

        command = SendMessageCommand(
            session_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            user_id=user.id,
            content="질문입니다.",
        )

        with pytest.raises(HTTPException) as exc_info:
            await use_case.execute(command)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_other_user_session_raises_404(self):
        other_signup = {**_SIGNUP, "email": "msg_other@example.com", "phone_number": "01011110000"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers_a = await _get_auth_headers(client)
            session_id = await _create_session(client, headers_a)

            await client.post("/api/v1/auth/signup", json=other_signup)
            user_b = await User.get(email=other_signup["email"])

        session_repo = TortoiseChatSessionRepository()
        message_repo = TortoiseChatMessageRepository()
        use_case = StreamMessageUseCase(session_repo, message_repo, StubLLMClient())

        command = SendMessageCommand(
            session_id=uuid.UUID(session_id),
            user_id=user_b.id,
            content="질문입니다.",
        )

        with pytest.raises(HTTPException) as exc_info:
            await use_case.execute(command)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_context_included_in_llm_call(self):
        """이전 대화 맥락이 LLM 호출에 포함되는지 확인."""
        captured: list[list[dict]] = []

        async def fake_stream(self, messages: list[dict], system_prompt: str) -> AsyncGenerator[str, None]:
            captured.append(messages)
            yield "답변입니다."

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            session_id = await _create_session(client, headers)
            user = await User.get(email=_SIGNUP["email"])

        session_repo = TortoiseChatSessionRepository()
        message_repo = TortoiseChatMessageRepository()

        with patch.object(StubLLMClient, "stream", new=fake_stream):
            use_case = StreamMessageUseCase(session_repo, message_repo, StubLLMClient())

            # 첫 번째 메시지
            cmd = SendMessageCommand(session_id=uuid.UUID(session_id), user_id=user.id, content="첫 번째 질문")
            async for _ in await use_case.execute(cmd):
                pass

            captured.clear()

            # 두 번째 메시지 — 첫 번째 대화가 맥락에 포함되어야 함
            cmd2 = SendMessageCommand(session_id=uuid.UUID(session_id), user_id=user.id, content="두 번째 질문")
            async for _ in await use_case.execute(cmd2):
                pass

        assert len(captured) == 1
        roles = [m["role"] for m in captured[0]]
        assert "user" in roles
        assert "assistant" in roles
