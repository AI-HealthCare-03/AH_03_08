from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class ChatSession:
    user_id: int
    id: UUID = field(default_factory=uuid4)
    guide_id: UUID | None = None
    title: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    last_active_at: datetime = field(default_factory=datetime.now)


@dataclass
class ChatMessage:
    session_id: UUID
    role: str  # "user" | "assistant"
    content: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
