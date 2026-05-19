# 표준 라이브러리
import os

# 서드파티 라이브러리
import httpx
from celery.utils.log import get_task_logger

# 로컬 모듈
from ai_worker.core.config import Config

# 로거 설정
logger = get_task_logger(__name__)

# 환경변수 초기화
config = Config()


async def _call_openai_tts(text: str) -> bytes:
    """
    OpenAI TTS API를 호출하여 음성 데이터를 반환한다.

    Args:
        text: 변환할 텍스트
              (GUIDES.medication_guide_summary 또는 GUIDES.lifestyle_guide_summary)

    Returns:
        bytes: MP3 음성 데이터

    Note:
        - OPENAI_API_KEY는 반드시 .env에서 관리 (하드코딩 금지)
        - 개인정보 보호: 텍스트 내용 직접 로그 출력 금지, 길이만 기록
    """
    from openai import AsyncOpenAI

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

    logger.info(f"OpenAI TTS API 호출 시작 - 텍스트 길이: {len(text)}자")

    client = AsyncOpenAI(api_key=api_key)

    response = await client.audio.speech.create(
        model="tts-1",       # 빠른 TTS 모델
        voice="nova",        # 한국어에 적합한 자연스러운 목소리
        input=text,
        response_format="mp3",
    )

    logger.info("OpenAI TTS API 호출 완료")
    return response.content
