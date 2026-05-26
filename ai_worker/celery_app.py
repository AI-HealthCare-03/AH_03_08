import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "medilog_ai",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "ai_worker.tasks.llm_tasks",
        "ai_worker.tasks.tts_tasks",
        "ai_worker.tasks.tts_task",
        "ai_worker.tasks.image_task",
        "ai_worker.tasks.image_tasks",
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
        "ai_worker.tasks.llm_tasks.*": {"queue": "llm"},
        "ai_worker.tasks.tts_tasks.*": {"queue": "tts"},
        "ai_worker.tasks.tts_task.*": {"queue": "tts"},
        "ai_worker.tasks.image_task.*": {"queue": "image"},
        "ai_worker.tasks.image_tasks.*": {"queue": "image"},
    },
    beat_schedule={
        "daily-tip-every-morning": {
            "task": "ai_worker.tasks.llm_tasks.generate_daily_tip_scheduled",
            "schedule": 86400.0,
            "options": {"queue": "llm"},
        },
    },
)
