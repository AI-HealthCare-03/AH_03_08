import os
import zoneinfo
from enum import StrEnum
from pathlib import Path

from pydantic import field_validator
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

    # [수정 8] 운영 환경에서 env 미설정 시 명시적 오류 발생
    # 기존: f"default-secret-key{uuid.uuid4().hex}" → 재시작마다 키 변경 → 기존 JWT 전부 무효화
    SECRET_KEY: str = ""

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def require_secret_key(cls, v: str, info) -> str:
        env = (info.data or {}).get("ENV", Env.LOCAL)
        if env == Env.PROD and not v:
            raise ValueError("운영 환경(ENV=prod)에서 SECRET_KEY는 반드시 설정해야 합니다.")
        # 로컬·개발 환경은 고정 기본값 사용 (재시작해도 동일)
        return v or "local-dev-secret-key-change-in-prod"

    @property
    def TIMEZONE(self) -> zoneinfo.ZoneInfo:  # noqa: N802
        return zoneinfo.ZoneInfo("Asia/Seoul")

    TEMPLATE_DIR: str = os.path.join(Path(__file__).resolve().parent.parent, "templates")

    # DB
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "pw1234"
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

    # Pill Classification
    PILL_MODEL_PATH: str = ""
    PILL_LABEL_PATH: str = ""
    PILL_DATA_PATH: str = ""

    # [수정 6] Redis 싱글톤에서 사용할 URL 필드 추가
    # WebSocket 핸들러가 매 연결마다 aioredis.from_url()을 호출하던 문제 해결
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    UPLOAD_DIR: str = "/tmp/uploads"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # [12] Worker → FastAPI 내부 콜백 인증 시크릿
    # 운영 환경에서는 .env에 강력한 랜덤 문자열로 설정
    INTERNAL_SECRET: str = "local-internal-secret-change-in-prod"

    # [수정 8] CORS — 환경별 허용 출처
    # 운영 환경에서는 .env의 ALLOWED_ORIGINS에 실제 도메인을 콤마 구분으로 설정
    # 예: ALLOWED_ORIGINS=https://medilog.vercel.app,https://www.medilog.com
    ALLOWED_ORIGINS: str = ""

    def get_allowed_origins(self) -> list[str]:
        """환경별 CORS 허용 출처 반환."""
        if self.ALLOWED_ORIGINS:
            return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
        if self.ENV == Env.PROD:
            return []   # 운영 환경에서 ALLOWED_ORIGINS 미설정 시 전체 차단
        return [        # 로컬·개발 환경 기본값
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
        ]


config = Config()