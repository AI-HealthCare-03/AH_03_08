# ai_worker/main.py

# 로컬 모듈
from ai_worker.tasks.tts_task import celery_app

# Celery 워커 실행 진입점
# 이 파일을 통해 Celery가 tts_task를 인식하고 실행함
if __name__ == "__main__":
    celery_app.worker_main()