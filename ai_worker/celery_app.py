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
    # [수정] 실제 파일 위치 ai_worker/tasks/ 에 맞게 경로 통일
    # 변경 전: "ai_worker.task.*" (단수, 존재하지 않는 경로)
    # 변경 후: "ai_worker.tasks.*" (복수, 실제 디렉터리)
    include=[
        "ai_worker.task.ocr_task",
        "ai_worker.task.llm_tasks",
        "ai_worker.task.tts_task",
        "ai_worker.task.image_task",
        "ai_worker.task.ai_tasks",
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
    # [수정] task_routes 패턴을 실제 태스크 name= 값과 일치시킴
    # OCR:   name="ai_worker.task.ocr_task.*"   (단수 .task)
    # LLM:   name="ai_worker.task.llm_tasks.*"  (단수 .task, 복수 llm_tasks)
    # TTS:   name="ai_worker.tasks.tts_task.*"  (복수 .tasks)
    # Image: name="ai_worker.tasks.image_task.*"(복수 .tasks)
    task_routes={
        "ai_worker.task.ocr_task.*": {"queue": "image"},
        "ai_worker.task.llm_tasks.*": {"queue": "llm"},
        "ai_worker.task.tts_task.*": {"queue": "tts"},
        "ai_worker.task.image_task.*": {"queue": "image"},
        "ai_worker.task.ai_tasks.*": {"queue": "llm"},
    },
    beat_schedule={
        "daily-tip-every-morning": {
            "task": "ai_worker.task.llm_tasks.generate_daily_tip_scheduled",
            "schedule": 86400.0,
            "options": {"queue": "llm"},
        },
    },
)