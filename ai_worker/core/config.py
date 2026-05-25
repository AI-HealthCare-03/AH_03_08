import zoneinfo
from dataclasses import field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    TIMEZONE: zoneinfo.ZoneInfo = field(default_factory=lambda: zoneinfo.ZoneInfo("Asia/Seoul"))

    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    OCR_PROVIDER: str = "clova"
    CLOVA_OCR_URL: str = ""
    CLOVA_OCR_SECRET: str = ""

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "ozcoding"
    DB_PASSWORD: str = ""
    DB_NAME: str = "ai_health"

    OPENAI_API_KEY: str = ""
