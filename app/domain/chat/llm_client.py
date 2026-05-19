from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class AbstractLLMClient(ABC):
    @abstractmethod
    def stream(self, messages: list[dict], system_prompt: str) -> AsyncGenerator[str, None]: ...
