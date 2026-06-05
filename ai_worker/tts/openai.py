# 표준 라이브러리
import logging

# 서드파티 라이브러리
from openai import AsyncOpenAI

# 로컬 모듈
from ai_worker.tts.base import TTSProvider

logger = logging.getLogger(__name__)


class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS API를 활용한 텍스트 → 음성 변환 구현체."""

    def __init__(self, api_key: str) -> None:
        self.client = AsyncOpenAI(api_key=api_key)

    async def convert_text_to_speech(self, text: str) -> bytes:
        """텍스트를 MP3 음성 데이터로 변환한다.

        Args:
            text: 변환할 텍스트

        Returns:
            bytes: MP3 음성 데이터

        Note:
            - 개인정보 보호: 텍스트 내용 직접 로그 출력 금지, 길이만 기록
        """
        logger.info(f"OpenAI TTS 변환 시작 - 텍스트 길이: {len(text)}자")
        response = await self.client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
            response_format="mp3",
        )
        logger.info("OpenAI TTS 변환 완료")
        return response.content
