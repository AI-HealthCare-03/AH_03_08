from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from app.core import config

TORTOISE_APP_MODELS = [
    "aerich.models",
    "app.models.users",
    "app.models.medical_records",
    "app.models.guides",
    "app.models.medications",
    "app.models.underlying_diseases",
    "app.models.allergies",
    "app.models.chat_sessions",
    "app.models.chat_messages",
    "app.models.calendar_events",
    "app.models.notifications",
    "app.models.guide_assets",
    "app.models.feedbacks",
    "app.models.feedback_tags",
    "app.models.access_logs",        # 추가
    "app.models.error_logs",         # 추가
    "app.models.audit_logs",         # 추가
    "app.models.model_metrics",      # 추가 (ModelMetric + MetricSnapshot 둘 다 포함)
]
TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "dialect": "asyncmy",
            "credentials": {
                "host": config.DB_HOST,
                "port": config.DB_PORT,
                "user": config.DB_USER,
                "password": config.DB_PASSWORD,
                "database": config.DB_NAME,
                "connect_timeout": config.DB_CONNECT_TIMEOUT,
                "maxsize": config.DB_CONNECTION_POOL_MAXSIZE,
            },
        },
    },
    "apps": {
        "models": {
            "models": TORTOISE_APP_MODELS,
        },
    },
    "timezone": "Asia/Seoul",
}


def initialize_tortoise(app: FastAPI) -> None:
    Tortoise.init_models(TORTOISE_APP_MODELS, "models")
    register_tortoise(app, config=TORTOISE_ORM)
