# 표준 라이브러리
import asyncio
import os

# 서드파티 라이브러리
import httpx
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
        tts_audio = asyncio.run(_call_clova_tts(summary_text))

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

async def _call_clova_tts(text: str) -> bytes:
    """
    CLOVA TTS API를 호출하여 음성 데이터를 반환한다.

    GUIDES 테이블의 medication_guide 또는 lifestyle_guide 텍스트를
    입력받아 MP3 음성 데이터로 변환한다. (REQ-GUIDE-002 연동)

    Args:
        text: 변환할 텍스트
              (GUIDES.medication_guide 또는 GUIDES.lifestyle_guide)

    Returns:
        bytes: MP3 음성 데이터

    Note:
        - CLOVA_TTS_API_KEY, CLOVA_TTS_API_URL은 반드시 .env에서 관리 (하드코딩 금지)
        - 개인정보 보호: 텍스트 내용 직접 로그 출력 금지, 길이만 기록
        - 의료 데이터 특성상 텍스트 내용 외부 노출 주의
    """
    # .env에서 CLOVA API 접속 정보 읽기
    api_url = os.getenv("CLOVA_TTS_API_URL")
    api_key = os.getenv("CLOVA_TTS_API_KEY")

    # 환경변수 누락 시 명확한 오류 메시지 반환
    if not api_url or not api_key:
        raise ValueError("CLOVA_TTS_API_URL 또는 CLOVA_TTS_API_KEY 환경변수가 설정되지 않았습니다.")

    # 개인정보 보호: 텍스트 내용 대신 길이만 로그에 기록
    logger.info(f"CLOVA TTS API 호출 시작 - 텍스트 길이: {len(text)}자")

    # headers: CLOVA 서버에 인증 정보 및 데이터 형식 전달
    headers = {
        "Authorization": f"Bearer {api_key}",  # CLOVA API 키 인증
        "Content-Type": "application/json",     # JSON 형식으로 전송
    }

    # payload: CLOVA TTS 변환 설정값
    payload = {
        "text": text,       # GUIDES 테이블에서 가져온 가이드 요약본 텍스트
        "speaker": "nara",  # 한국어 여성 목소리 (복약 안내에 적합한 화자)
        "speed": 0,         # 읽기 속도 (0 = 기본 속도)
        "format": "mp3",    # 출력 파일 형식
    }

    # AsyncClient: 비동기 HTTP 클라이언트 (with 블록 종료 시 연결 자동 해제)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30.0,  # 30초 이내 응답 없으면 오류 처리
        )
        # HTTP 오류 상태코드(4xx, 5xx) 발생 시 예외 발생
        response.raise_for_status()

    logger.info("CLOVA TTS API 호출 완료")

    # MP3 음성 데이터(bytes) 반환 → 다음 브랜치(feature/tts-s3-upload)에서 S3 업로드
    return response.content
