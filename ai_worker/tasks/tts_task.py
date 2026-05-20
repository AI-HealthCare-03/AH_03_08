# 표준 라이브러리
import asyncio
import os
import uuid  # S3 파일명 중복 방지용 고유 ID 생성

# 서드파티 라이브러리
import boto3
from celery import Celery
from celery.utils.log import get_task_logger
from tortoise import Tortoise

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
def convert_text_to_speech(self, guide_id: str, summary_text: str, user_id: str, asset_type: str) -> dict:
    """
    GUIDES 테이블의 요약본 텍스트를 음성 파일(MP3)로 변환하는 Celery Task.

    REQ-GUIDE-002 연동: 지민님 LLM 파트에서 생성한 가이드 요약본을
    CLOVA TTS로 변환 후 S3에 저장한다. (asset_type=tts)

    Args:
        guide_id: GUIDES 테이블의 guide_id (GUIDE_ASSETS 테이블 연동용)
        summary_text: GUIDES.medication_guide_summary 또는 GUIDES.lifestyle_guide_summary
        user_id: 요청한 사용자 ID (S3 경로 구분 및 개인정보 접근 분리용)
        asset_type: "tts_medication" 또는 "tts_lifestyle"

    Returns:
        dict: { "success": bool, "data": { "s3_url": s3_url,  }, "message": str }

    Note:
        - 개인정보 보호: 의료 데이터(summary_text) 로그 직접 출력 금지
        - S3 URL은 이후 GUIDE_ASSETS 테이블에 저장 예정 (팀장 DB 연동 후)
    """

    try:
        logger.info(f"TTS 변환 시작 - guide_id: {guide_id}, user_id: {user_id}")

        # 변환된 MP3 데이터를 S3에 업로드 → URL 반환
        s3_url = asyncio.run(_process_tts(summary_text, user_id, guide_id, asset_type))
        logger.info(f"TTS 변환 완료 - guide_id: {guide_id}")
        return {
            "success": True,
            "data": {
                "guide_id": guide_id,
                "asset_type": asset_type,
                "s3_url": s3_url,
            },
            "message": "TTS 변환이 완료되었습니다.",
        }
    except Exception as exc:
        logger.error(f"TTS 변환 실패 - guide_id: {guide_id}, error: {exc}")
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
        Bucket=bucket_name,  # 업로드할 S3 버킷 이름
        Key=file_key,  # S3 내 저장 경로 + 파일명
        Body=audio_data,  # 실제 MP3 데이터
        ContentType="audio/mpeg",  # 파일 형식 명시
    )

    # S3 URL 조합: 이 URL을 app/ 파트에서 GUIDE_ASSETS 테이블에 저장
    return f"https://{bucket_name}.s3.{region}.amazonaws.com/{file_key}"


async def _process_tts(summary_text: str, user_id: str, guide_id: str, asset_type: str) -> str:
    """
    TTS 변환 → S3 업로드 → DB 저장을 순서대로 처리한다.

    Returns:
        str: S3 파일 URL
    """
    # 1. CLOVA TTS 변환
    tts_audio = await _call_openai_tts(summary_text)

    # 2. S3 업로드 (동기 함수 - async 안에서 직접 호출 가능)
    s3_url = _upload_to_s3(tts_audio, user_id)

    # 3. GUIDE_ASSETS 테이블에 URL 저장
    # TODO: 팀장님 feature/db-models-and-api merge 후 주석 해제
    # await _save_guide_asset_to_db(guide_id, asset_type, s3_url)

    return s3_url


async def _save_guide_asset_to_db(guide_id: str, asset_type: str, file_url: str) -> None:
    """
    S3 URL을 GUIDE_ASSETS 테이블에 저장한다.

    Args:
        guide_id: GUIDES 테이블의 guide_id (FK)
        asset_type: "tts_medication" 또는 "tts_lifestyle"
        file_url: S3에 업로드된 MP3 파일 URL

    Note:
        - ai_worker는 FastAPI와 별도 컨테이너라 Tortoise.init()으로 직접 DB 연결
        - 팀장님 feature/db-models-and-api merge 후 연동 예정
    """
    # TODO: 팀장님 브랜치 merge 후 아래 import 주석 해제
    # from app.models.guide_assets import GuideAsset

    db_url = (
        f"mysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}"
        f"/{os.getenv('DB_NAME')}"
    )

    try:
        await Tortoise.init(
            db_url=db_url,
            modules={"models": ["app.models.guide_assets"]},
        )

        # TODO: 팀장님 브랜치 merge 후 주석 해제
        # await GuideAsset.create(
        #     id=uuid.uuid4(),
        #     guide_id=guide_id,
        #     asset_type=asset_type,
        #     file_url=file_url,
        # )

        logger.info(f"GUIDE_ASSETS 저장 완료 - guide_id: {guide_id}, asset_type: {asset_type}")

    finally:
        await Tortoise.close_connections()
