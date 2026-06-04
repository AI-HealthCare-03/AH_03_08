import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

BROKER_URL = os.getenv("CELERY_BROKER_URL")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND")

celery_app = Celery(
    "medilog_ai",
    broker=BROKER_URL,
    backend=BACKEND_URL,
    include=[
        "ai_worker.tasks.ocr_task",
        "ai_worker.tasks.llm_task",
        "ai_worker.tasks.image_task",
        "ai_worker.tasks.ai_task",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    task_routes={
        "ai_worker.tasks.ocr_task.*": {"queue": "image"},
        "ai_worker.tasks.llm_task.*": {"queue": "llm"},
        "ai_worker.tasks.image_task.*": {"queue": "image"},
        "ai_worker.tasks.ai_task.*": {"queue": "llm"},
    },
)

celery_app.conf.beat_schedule = {
    "daily-tip-every-morning": {
        "task": "ai_worker.tasks.llm_task.generate_daily_tip_scheduled",
        "schedule": 86400.0,
        "options": {"queue": "llm"},
    },
    "check-notifications-every-minute": {
        "task": "ai_worker.tasks.llm_task.check_and_send_notifications",
        "schedule": 60.0,
        "options": {"queue": "llm"},
    },
}