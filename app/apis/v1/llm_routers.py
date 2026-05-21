import json
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.llm import (
    ChatMessageListResponse,
    ChatMessageResponse,
    ChatMessageSendRequest,
    ChatSessionListResponse,
    ChatSessionResponse,
    RecordCreateRequest,
    RecordListResponse,
    RecordResponse,
)
from app.models.users import User
from app.services.llm_service import ChatService, MedicalRecordService

record_router = APIRouter(prefix="/records", tags=["records"])
chat_router = APIRouter(prefix="/chat", tags=["chat"])


# ════════════════════════════════════════
# MedicalRecord
# ════════════════════════════════════════


@record_router.post("", status_code=status.HTTP_201_CREATED)
async def create_record(
    body: RecordCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MedicalRecordService, Depends(MedicalRecordService)],
) -> Response:
    record = await service.create_record(
        user_id=user.id,
        record_type=body.record_type,
        file_url=body.file_url,
    )
    return Response(RecordResponse.model_validate(record).model_dump(), status_code=status.HTTP_201_CREATED)


@record_router.get("", status_code=status.HTTP_200_OK)
async def get_record_list(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MedicalRecordService, Depends(MedicalRecordService)],
    page: int = 1,
    limit: int = 20,
) -> Response:
    total, items = await service.get_record_list(user.id, page, limit)
    return Response(
        RecordListResponse(
            total=total,
            page=page,
            items=[RecordResponse.model_validate(r).model_dump() for r in items],
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@record_router.get("/{record_id}", status_code=status.HTTP_200_OK)
async def get_record(
    record_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MedicalRecordService, Depends(MedicalRecordService)],
) -> Response:
    record = await service.get_record(record_id, user.id)
    return Response(RecordResponse.model_validate(record).model_dump(), status_code=status.HTTP_200_OK)


# ════════════════════════════════════════
# Chat
# ════════════════════════════════════════


@chat_router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChatService, Depends(ChatService)],
) -> Response:
    session = await service.create_session(user_id=user.id)
    ws_url = f"wss://api.medilog.com/api/v1/chat/ws/{session.id}"
    return Response(
        {
            "id": session.id,
            "created_at": session.created_at.isoformat(),
            "ws_url": ws_url,
        },
        status_code=status.HTTP_201_CREATED,
    )


@chat_router.get("/sessions", status_code=status.HTTP_200_OK)
async def get_session_list(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChatService, Depends(ChatService)],
) -> Response:
    sessions = await service.get_session_list(user_id=user.id)
    return Response(
        {
            "sessions": [
                {
                    "id": s.id,
                    "created_at": s.created_at.isoformat(),
                    "ws_url": f"wss://api.medilog.com/api/v1/chat/ws/{s.id}",
                }
                for s in sessions
            ]
        },
        status_code=status.HTTP_200_OK,
    )


@chat_router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChatService, Depends(ChatService)],
) -> Response:
    await service.delete_session(session_id=session_id, user_id=user.id)
    return Response(None, status_code=status.HTTP_204_NO_CONTENT)


@chat_router.get("/sessions/{session_id}/messages", status_code=status.HTTP_200_OK)
async def get_message_list(
    session_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChatService, Depends(ChatService)],
    limit: int = 20,
    cursor: int | None = None,
) -> Response:
    messages = await service.get_message_list(session_id=session_id, user_id=user.id, limit=limit, cursor=cursor)
    next_cursor = messages[-1].id if len(messages) == limit else None
    return Response(
        ChatMessageListResponse(
            messages=[ChatMessageResponse.model_validate(m).model_dump() for m in messages],
            next_cursor=next_cursor,
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@chat_router.post("/sessions/{session_id}/messages", status_code=status.HTTP_202_ACCEPTED)
async def send_message(
    session_id: int,
    body: ChatMessageSendRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChatService, Depends(ChatService)],
) -> Response:
    assistant_msg = await service.send_message(session_id=session_id, user_id=user.id, message=body.message)
    return Response(
        ChatMessageResponse.model_validate(assistant_msg).model_dump(),
        status_code=status.HTTP_202_ACCEPTED,
    )


# ════════════════════════════════════════
# WebSocket — LLM 스트리밍
# ════════════════════════════════════════


@chat_router.websocket("/ws/{session_id}")
async def websocket_chat_stream(websocket: WebSocket, session_id: int):
    """
    Redis Pub/Sub 구독 → 토큰 단위로 클라이언트에 스트리밍
    LLM Worker가 Redis에 publish → 여기서 받아서 WebSocket으로 전달
    """
    await websocket.accept()

    import redis.asyncio as aioredis

    from app.core import config

    redis_url = getattr(config, "REDIS_URL", "redis://redis:6379/0")
    redis = aioredis.from_url(redis_url, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"chat:stream:{session_id}")

    try:
        async for raw_message in pubsub.listen():
            if raw_message["type"] != "message":
                continue
            data = json.loads(raw_message["data"])
            await websocket.send_json(data)
            # done 또는 error 신호가 오면 종료
            if data.get("done") or data.get("error"):
                break
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"chat:stream:{session_id}")
        await pubsub.aclose()
        await redis.aclose()
