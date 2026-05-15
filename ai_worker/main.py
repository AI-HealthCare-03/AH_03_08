from celery import Celery
from ai_worker.core.config import Config

config = Config()

celery_app = Celery(
    "ai_worker",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
    include=["ai_worker.tasks.ai_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_soft_time_limit=300,
    task_time_limit=360,
    result_expires=86400,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    timezone="Asia/Seoul",
    enable_utc=True,
)