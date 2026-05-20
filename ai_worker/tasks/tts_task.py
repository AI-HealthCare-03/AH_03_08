# 표준 라이브러리
import asyncio
import os

# 서드파티 라이브러리
from celery import Celery
from celery.utils.log import get_task_logger

# 로컬 모듈
from ai_worker.core.config import Config

# 로거 설정
logger = get_task_logger(__name__)

# 환경변수 초기화
config = Config()

# Celery 앱 초기화
celery_app = Celery(
    "tts_worker",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)


@celery_app.task(bind=True, max_retries=3)
def convert_text_to_speech(self, guide_id: str, summary_text: str, user_id: str) -> dict:
    try:
        logger.info(f"TTS 변환 시작 - guide_id: {guide_id}, user_id: {user_id}")
        tts_audio = asyncio.run(_call_openai_tts(summary_text))
        logger.info(f"TTS 변환 완료 - guide_id: {guide_id}")
        return {
            "success": True,
            "data": {
                "guide_id": guide_id,
                "tts_audio_size": len(tts_audio),
            },
            "message": "TTS 변환이 완료되었습니다.",
        }
    except Exception as exc:
        logger.error(f"TTS 변환 실패 - guide_id: {guide_id}, error: {exc}")
        raise self.retry(exc=exc, countdown=10) from exc


async def _call_openai_tts(text: str) -> bytes:
    from openai import AsyncOpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

    logger.info(f"OpenAI TTS API 호출 시작 - 텍스트 길이: {len(text)}자")
    client = AsyncOpenAI(api_key=api_key)
    response = await client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=text,
        response_format="mp3",
    )
    logger.info("OpenAI TTS API 호출 완료")
    return response.content