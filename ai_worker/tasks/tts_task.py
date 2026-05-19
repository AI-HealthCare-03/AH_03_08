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
# "tts_worker" → 이 워커의 이름
# broker → Redis가 중간에서 작업을 전달해주는 메시지 브로커 역할
celery_app = Celery(
    "tts_worker",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)


# -------------------------
# Celery Task (이번 브랜치 핵심)
# -------------------------


# @celery_app.task → 이 함수를 Celery가 처리할 Task로 등록
# bind=True → self(현재 Task 자신)를 참조 → self.retry() 호출 가능
# max_retries=3 → 실패 시 최대 3번까지 재시도
@celery_app.task(bind=True, max_retries=3)
def convert_text_to_speech(self, guide_id: str, summary_text: str, user_id: str) -> dict:
    """
    GUIDES 테이블의 요약본 텍스트를 음성 파일(MP3)로 변환하는 Celery Task.

    REQ-GUIDE-002 연동: 지민님 LLM 파트에서 생성한 가이드 요약본을
    CLOVA TTS로 변환 후 S3에 저장한다. (asset_type=tts)

    Args:
        guide_id: GUIDES 테이블의 guide_id (GUIDE_ASSETS 테이블 연동용)
        summary_text: GUIDES.medication_guide 또는 GUIDES.lifestyle_guide 텍스트
        user_id: 요청한 사용자 ID (S3 경로 구분 및 개인정보 접근 분리용)

    Returns:
        dict: { "success": bool, "data": { "s3_url": str }, "message": str }

    Note:
        - 개인정보 보호: 의료 데이터(summary_text) 로그 직접 출력 금지
        - S3 URL은 이후 GUIDE_ASSETS 테이블에 저장 예정 (팀장 DB 연동 후)
    """

    try:
        # 작업 시작 로그 (개인정보 보호: 텍스트 내용 직접 출력 금지)
        logger.info(f"TTS 변환 시작 - guide_id: {guide_id}, user_id: {user_id}")

        # 비동기 함수를 Celery(동기) 환경에서 실행하기 위해 asyncio.run() 사용
        tts_audio = asyncio.run(_call_openai_tts(summary_text))

        # 변환된 MP3 데이터를 S3에 업로드 → URL 반환
        # S3 업로드는 다음 브랜치(feature/tts-s3-upload)에서 구현 예정
        # 현재는 tts_audio(bytes) 반환까지만 처리
        logger.info(f"TTS 변환 완료 - guide_id: {guide_id}")

        # 팀 규칙: API 응답은 { success, data, message } 구조 유지
        return {
            "success": True,
            "data": {
                "guide_id": guide_id,
                "tts_audio_size": len(tts_audio),  # 디버깅용 (실제 URL은 S3 업로드 후 반환)
            },
            "message": "TTS 변환이 완료되었습니다.",
        }

    except Exception as exc:
        # 개인정보 보호: 에러 로그에 텍스트 내용 출력 금지
        logger.error(f"TTS 변환 실패 - guide_id: {guide_id}, error: {exc}")
        # countdown=10 → 10초 후 재시도 / max_retries=3 초과 시 최종 실패
        raise self.retry(exc=exc, countdown=10) from exc


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
        model="tts-1",
        voice="nova",
        input=text,
        response_format="mp3",
    )

    logger.info("OpenAI TTS API 호출 완료")
    return response.content