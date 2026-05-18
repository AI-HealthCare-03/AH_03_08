from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class CreateSessionCommand:
    user_id: int
    guide_id: UUID | None = None
    title: str | None = None


@dataclass
class SendMessageCommand:
    session_id: UUID
    user_id: int
    content: str
    allergies: list[str] = field(default_factory=list)
    underlying_diseases: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
