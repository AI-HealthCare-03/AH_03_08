import csv
import json
import os
from functools import lru_cache
from typing import Annotated
from uuid import UUID

_KCD_CSV = "/app/data/kcd/건강보험심사평가원_상병마스터.csv"


@lru_cache(maxsize=1)
def _load_kcd() -> dict[str, str]:
    if not os.path.exists(_KCD_CSV):
        return {}
    result: dict[str, str] = {}
    with open(_KCD_CSV, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            code = row["상병기호"].strip()
            if code and code not in result:
                result[code] = row["한글명"].strip()
    return result


def _kcd_name(code: str) -> str | None:
    return _load_kcd().get(code)

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status

from app.application.chat.dto.chat_dto import CreateSessionCommand, SendMessageCommand
from app.application.chat.use_cases.create_session import CreateSessionUseCase
from app.application.chat.use_cases.delete_session import DeleteSessionUseCase
from app.application.chat.use_cases.get_session import GetSessionUseCase
from app.application.chat.use_cases.list_sessions import ListSessionsUseCase
from app.application.chat.use_cases.stream_message import StreamMessageUseCase
from app.dependencies.security import get_request_user
from app.domain.chat.llm_client import AbstractLLMClient
from app.domain.chat.repository import AbstractChatMessageRepository, AbstractChatSessionRepository
from app.infrastructure.chat.llm_client import OpenAILLMClient
from app.infrastructure.chat.repository import TortoiseChatMessageRepository, TortoiseChatSessionRepository
from app.models.allergies import Allergy
from app.models.underlying_diseases import UnderlyingDisease
from app.models.users import User
from app.presentation.api.v1.chats.schemas import (
    CreateSessionRequestSchema,
    MessageListResponseSchema,
    MessageResponseSchema,
    SessionListResponseSchema,
    SessionResponseSchema,
)
from app.services.jwt import JwtService

chats_router = APIRouter(prefix="/chats", tags=["chats"])


def get_chat_session_repository() -> AbstractChatSessionRepository:
    return TortoiseChatSessionRepository()


def get_chat_message_repository() -> AbstractChatMessageRepository:
    return TortoiseChatMessageRepository()


def get_llm_client() -> AbstractLLMClient:
    return OpenAILLMClient()


def get_create_session_use_case(
    repo: Annotated[AbstractChatSessionRepository, Depends(get_chat_session_repository)],
) -> CreateSessionUseCase:
    return CreateSessionUseCase(repo)


def get_list_sessions_use_case(
    repo: Annotated[AbstractChatSessionRepository, Depends(get_chat_session_repository)],
) -> ListSessionsUseCase:
    return ListSessionsUseCase(repo)


def get_get_session_use_case(
    repo: Annotated[AbstractChatSessionRepository, Depends(get_chat_session_repository)],
) -> GetSessionUseCase:
    return GetSessionUseCase(repo)


def get_delete_session_use_case(
    repo: Annotated[AbstractChatSessionRepository, Depends(get_chat_session_repository)],
) -> DeleteSessionUseCase:
    return DeleteSessionUseCase(repo)


def get_stream_message_use_case(
    session_repo: Annotated[AbstractChatSessionRepository, Depends(get_chat_session_repository)],
    message_repo: Annotated[AbstractChatMessageRepository, Depends(get_chat_message_repository)],
    llm_client: Annotated[AbstractLLMClient, Depends(get_llm_client)],
) -> StreamMessageUseCase:
    return StreamMessageUseCase(session_repo, message_repo, llm_client)


async def _build_guide_context(session_id: int) -> str:
    from app.models.chat_sessions import ChatSession as ChatSessionORM
    from app.models.guide import Guide

    session = await ChatSessionORM.get_or_none(id=session_id)
    if not session or not session.guide_id:
        return ""
    guide = await Guide.get_or_none(id=session.guide_id)
    if not guide:
        return ""
    parts = []
    if guide.summary_text:
        parts.append(f"요약: {guide.summary_text}")
    if guide.medication_guide:
        parts.append(f"복약 안내: {guide.medication_guide}")
    if guide.lifestyle_guide:
        parts.append(f"생활 습관: {guide.lifestyle_guide}")
    try:
        record = await guide.record
        if record and record.parsed_data:
            disease_code = record.parsed_data.get("disease_code")
            if disease_code:
                name = _kcd_name(disease_code)
                label = f"{name} ({disease_code})" if name else disease_code
                parts.append(f"진단명: {label} ← 이 명칭을 반드시 그대로 사용하세요")
            meds = record.parsed_data.get("medications", [])
            if meds:
                med_list = ", ".join(m.get("name", "") for m in meds if m.get("name"))
                parts.append(f"처방 약물: {med_list}")
    except Exception:
        pass
    return "\n".join(parts)


async def _get_ws_user(token: str) -> User | None:
    """WebSocket은 HTTPBearer를 쓸 수 없어서 JWT를 직접 검증한다."""
    try:
        verified = JwtService().verify_jwt(token=token, token_type="access")
        from app.repositories.user_repository import UserRepository

        return await UserRepository().get_user(verified.payload["user_id"])
    except Exception:
        return None


@chats_router.post("", response_model=SessionResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: CreateSessionRequestSchema,
    user: Annotated[User, Depends(get_request_user)],
    use_case: Annotated[CreateSessionUseCase, Depends(get_create_session_use_case)],
) -> SessionResponseSchema:
    command = CreateSessionCommand(user_id=user.id, guide_id=body.guide_id, title=body.title)
    session = await use_case.execute(command)
    return SessionResponseSchema.model_validate(session)


@chats_router.get("", response_model=SessionListResponseSchema, status_code=status.HTTP_200_OK)
async def list_sessions(
    user: Annotated[User, Depends(get_request_user)],
    use_case: Annotated[ListSessionsUseCase, Depends(get_list_sessions_use_case)],
    message_repo: Annotated[AbstractChatMessageRepository, Depends(get_chat_message_repository)],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> SessionListResponseSchema:
    sessions, total = await use_case.execute(user_id=user.id, page=page, limit=limit)
    items = []
    for session in sessions:
        messages = await message_repo.find_recent_by_session_id(session.id, limit=1)
        last = messages[0] if messages else None
        schema = SessionResponseSchema.model_validate(session)
        schema.last_message_content = last.content if last else None
        schema.last_message_role = last.role if last else None
        items.append(schema)
    return SessionListResponseSchema(total=total, page=page, items=items)


@chats_router.get("/{session_id}", response_model=SessionResponseSchema, status_code=status.HTTP_200_OK)
async def get_session(
    session_id: int,
    user: Annotated[User, Depends(get_request_user)],
    use_case: Annotated[GetSessionUseCase, Depends(get_get_session_use_case)],
) -> SessionResponseSchema:
    session = await use_case.execute(session_id=session_id, user_id=user.id)
    return SessionResponseSchema.model_validate(session)


@chats_router.get("/{session_id}/messages", response_model=MessageListResponseSchema, status_code=status.HTTP_200_OK)
async def list_messages(
    session_id: int,
    user: Annotated[User, Depends(get_request_user)],
    session_repo: Annotated[AbstractChatSessionRepository, Depends(get_chat_session_repository)],
    message_repo: Annotated[AbstractChatMessageRepository, Depends(get_chat_message_repository)],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> MessageListResponseSchema:
    session = await session_repo.find_by_id(session_id=session_id, user_id=user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="채팅 세션을 찾을 수 없습니다.")
    messages = await message_repo.find_recent_by_session_id(session_id=session_id, limit=limit)
    return MessageListResponseSchema(items=[MessageResponseSchema.model_validate(m) for m in reversed(messages)])


@chats_router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    user: Annotated[User, Depends(get_request_user)],
    use_case: Annotated[DeleteSessionUseCase, Depends(get_delete_session_use_case)],
) -> None:
    await use_case.execute(session_id=session_id, user_id=user.id)


@chats_router.websocket("/{session_id}/ws")
async def chat_websocket(
    websocket: WebSocket,
    session_id: int,
    token: str,
) -> None:
    """
    WebSocket 채팅 엔드포인트.
    연결: ws://host/api/v1/chats/{session_id}/ws?token=<access_token>
    클라이언트 → 서버: {"content": "질문 내용"}
    서버 → 클라이언트: {"type": "token", "content": "토큰"} (스트리밍)
    서버 → 클라이언트: {"type": "done"} (완료)
    서버 → 클라이언트: {"type": "error", "detail": "메시지"} (에러)
    """
    await websocket.accept()

    user = await _get_ws_user(token)
    if not user:
        await websocket.send_text(json.dumps({"type": "error", "detail": "인증에 실패했습니다."}))
        await websocket.close(code=4001)
        return

    # 세션의 가이드 컨텍스트를 연결 시점에 한 번만 로드
    guide_context = await _build_guide_context(session_id)

    use_case = StreamMessageUseCase(
        TortoiseChatSessionRepository(),
        TortoiseChatMessageRepository(),
        OpenAILLMClient(),
    )

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                content = data.get("content", "").strip()
            except (json.JSONDecodeError, AttributeError):
                await websocket.send_text(json.dumps({"type": "error", "detail": "잘못된 메시지 형식입니다."}))
                continue

            if not content:
                await websocket.send_text(json.dumps({"type": "error", "detail": "메시지 내용을 입력해주세요."}))
                continue

            allergies = await Allergy.filter(user_id=user.id).values_list("allergy_name", flat=True)
            diseases = await UnderlyingDisease.filter(user_id=user.id).values_list("underlying_disease_name", flat=True)

            command = SendMessageCommand(
                session_id=session_id,
                user_id=user.id,
                content=content,
                allergies=list(allergies),
                underlying_diseases=list(diseases),
                guide_context=guide_context,
            )

            try:
                generator = await use_case.execute(command)
                async for token in generator:
                    await websocket.send_text(json.dumps({"type": "token", "content": token}, ensure_ascii=False))
                await websocket.send_text(json.dumps({"type": "done"}))
            except Exception as e:
                await websocket.send_text(json.dumps({"type": "error", "detail": str(e)}))

    except WebSocketDisconnect:
        pass
