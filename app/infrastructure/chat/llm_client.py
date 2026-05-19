from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.core import config
from app.domain.chat.llm_client import AbstractLLMClient


class StubLLMClient(AbstractLLMClient):
    """OpenAI 키 없이 동작을 검증할 때 사용하는 더미 클라이언트."""

    async def stream(self, messages: list[dict], system_prompt: str) -> AsyncGenerator[str, None]:
        for word in "안녕하세요! 현재 AI 연동 준비 중입니다. OpenAI 키가 등록되면 실제 답변을 제공합니다.".split():
            yield word + " "


class OpenAILLMClient(AbstractLLMClient):
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

    async def stream(self, messages: list[dict], system_prompt: str) -> AsyncGenerator[str, None]:
        full_messages = [{"role": "system", "content": system_prompt}, *messages]
        response = await self._client.chat.completions.create(
            model=config.OPENAI_CHAT_MODEL,
            messages=full_messages,
            temperature=0,
            stream=True,
        )
        async for chunk in response:
            token = chunk.choices[0].delta.content
            if token:
                yield token
