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