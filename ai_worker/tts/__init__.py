from ai_worker.core.config import Config
from ai_worker.tts.base import TTSProvider
from ai_worker.tts.openai import OpenAITTSProvider


def get_tts_provider(config: Config) -> TTSProvider:
    return OpenAITTSProvider(
        api_key=config.OPENAI_API_KEY,
        bucket_name=config.S3_BUCKET_NAME,
        aws_access_key=config.AWS_ACCESS_KEY,
        aws_secret_key=config.AWS_SECRET_KEY,
        aws_region=config.AWS_REGION,
    )

