import os
import zoneinfo
from enum import StrEnum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(StrEnum):
    LOCAL = "local"
    DEV = "dev"
    PROD = "prod"


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENV: Env = Env.LOCAL
    SECRET_KEY: str  # 기본값 제거 — 반드시 .env에서 주입

    @property
    def TIMEZONE(self) -> zoneinfo.ZoneInfo:  # noqa: N802
        return zoneinfo.ZoneInfo("Asia/Seoul")

    TEMPLATE_DIR: str = os.path.join(Path(__file__).resolve().parent.parent, "templates")

    # DB
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "ozcoding"   # root → ozcoding
    DB_PASSWORD: str = ""       # pw1234 제거
    DB_NAME: str = "ai_health"
    DB_CONNECT_TIMEOUT: int = 5
    DB_CONNECTION_POOL_MAXSIZE: int = 10

    COOKIE_DOMAIN: str = "localhost"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 14 * 24 * 60
    JWT_LEEWAY: int = 5

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # OCR
    CLOVA_OCR_URL: str = ""
    CLOVA_OCR_SECRET: str = ""

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    UPLOAD_DIR: str = "/tmp/uploads"


config = Config()