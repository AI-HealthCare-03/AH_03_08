# 표준 라이브러리
import uuid

# 서드파티 라이브러리
import boto3
from celery.utils.log import get_task_logger
from openai import AsyncOpenAI

# 로컬 모듈
from ai_worker.tts.base import TTSProvider

logger = get_task_logger(__name__)


class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS API를 활용한 텍스트 → 음성 변환 구현체."""

    def __init__(
        self,
        api_key: str,
        bucket_name: str,
        aws_access_key: str,
        aws_secret_key: str,
        aws_region: str,
    ) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region,
        )
        self.bucket_name = bucket_name
        self.region = aws_region

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

    def upload_to_s3(self, audio_data: bytes, user_id: str) -> str:
        """MP3 음성 데이터를 S3에 업로드하고 URL을 반환한다.

        Args:
            audio_data: MP3 음성 데이터
            user_id: 사용자 ID (S3 경로 구분 및 개인정보 접근 분리용)

        Returns:
            str: S3 파일 URL

        Note:
            - 개인정보 보호: user_id 기반 경로로 사용자별 접근 분리
        """
        file_key = f"tts/{user_id}/{uuid.uuid4()}.mp3"

        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=file_key,
            Body=audio_data,
            ContentType="audio/mpeg",
        )

        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{file_key}"
