from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateSessionRequestSchema(BaseModel):
    guide_id: UUID | None = None
    title: str | None = None


class SessionResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: int
    guide_id: UUID | None = None
    title: str | None = None
    created_at: datetime
    last_active_at: datetime
    last_message_content: str | None = None
    last_message_role: str | None = None


class SessionListResponseSchema(BaseModel):
    total: int
    page: int
    items: list[SessionResponseSchema]


class SendMessageRequestSchema(BaseModel):
    content: str


class MessageResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: datetime


class MessageListResponseSchema(BaseModel):
    items: list[MessageResponseSchema]
