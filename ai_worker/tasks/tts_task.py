# 표준 라이브러리
import asyncio
import os
import uuid  # S3 파일명 중복 방지용 고유 ID 생성

# 서드파티 라이브러리
import boto3
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
        s3_url = _upload_to_s3(tts_audio, user_id)
        logger.info(f"TTS 변환 완료 - guide_id: {guide_id}")

        # 팀 규칙: API 응답은 { success, data, message } 구조 유지
        return {
            "success": True,
            "data": {
                "guide_id": guide_id,
                "s3_url": s3_url,  # DB 저장용 URL (팀장 연동 후 GUIDE_ASSETS에 저장)
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

def _upload_to_s3(audio_data: bytes, user_id: str) -> str:
    """
    음성 파일을 S3에 업로드하고 URL을 반환한다.

    Args:
        audio_data: MP3 음성 데이터 (bytes)
        user_id: 사용자 ID (S3 경로 구분용)

    Returns:
        str: S3 파일 URL

    Note:
        - AWS_ACCESS_KEY, AWS_SECRET_KEY, S3_BUCKET_NAME은 반드시 .env에서 관리
        - 개인정보 보호: user_id 기반 경로로 사용자별 접근 분리
    """

    # .env에서 S3 접속 정보 읽기
    bucket_name = os.getenv("S3_BUCKET_NAME")
    region = os.getenv("AWS_REGION", "ap-northeast-2")  # 기본값: 서울 리전

    # S3 파일 경로 구성
    # tts/{user_id}/ → 사용자별 폴더 분리 (개인정보 접근 분리 목적)
    # uuid.uuid4() → 랜덤 고유 ID → 같은 사용자가 여러 번 생성해도 파일명 겹치지 않음
    file_key = f"tts/{user_id}/{uuid.uuid4()}.mp3"

    # boto3 → AWS S3를 Python으로 제어하는 클라이언트 초기화
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
        region_name=region,
    )

    # S3에 MP3 파일 업로드
    s3_client.put_object(
        Bucket=bucket_name,       # 업로드할 S3 버킷 이름
        Key=file_key,             # S3 내 저장 경로 + 파일명
        Body=audio_data,          # 실제 MP3 데이터
        ContentType="audio/mpeg", # 파일 형식 명시
    )

    # S3 URL 조합: 이 URL을 app/ 파트에서 GUIDE_ASSETS 테이블에 저장
    return f"https://{bucket_name}.s3.{region}.amazonaws.com/{file_key}"
