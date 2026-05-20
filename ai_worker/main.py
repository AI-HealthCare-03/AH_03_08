<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> origin/feature/tts-s3-upload
from celery import Celery

from ai_worker.core.config import Config

config = Config()

celery_app = Celery(
    "ai_worker",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
    include=["ai_worker.tasks.ai_tasks", "ai_worker.tasks.ocr_task", "ai_worker.tasks.tts_task"],
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
<<<<<<< HEAD
=======
# ai_worker/main.py

# 로컬 모듈
from ai_worker.tasks.tts_task import celery_app

# Celery 워커 실행 진입점
# 이 파일을 통해 Celery가 tts_task를 인식하고 실행함
if __name__ == "__main__":
    celery_app.worker_main()
>>>>>>> origin/feature/tts-celery-task
=======
>>>>>>> origin/feature/tts-s3-upload
