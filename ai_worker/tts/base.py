from abc import ABC, abstractmethod


class TTSProvider(ABC):
    @abstractmethod
    async def convert_text_to_speech(self, text: str) -> bytes: ...

