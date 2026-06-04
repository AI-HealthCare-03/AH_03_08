# app/services/tts.py

# 서드파티 라이브러리
import asyncio
from openai import AsyncOpenAI

# 로컬 모듈
from app.core.config import config


class TtsService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

    async def create_tts_asset(
        self,
        summary_text: str,
    ) -> bytes:
        """
        TTS 음성 변환 요청을 처리하고 mp3 bytes를 반환한다.

        Args:
            summary_text: GUIDES.summary_text (복약+생활 통합 요약)

        Returns:
            bytes: MP3 음성 데이터

        Note:
            - 개인정보 보호: 의료 데이터(summary_text) 로그 직접 출력 금지
        """
        response = await self.client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=summary_text,
            response_format="mp3",
        )
        return response.content