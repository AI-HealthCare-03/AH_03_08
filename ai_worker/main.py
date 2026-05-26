import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

app = Celery(
    "ai_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
)

app.conf.task_routes = {
    "ai_worker.task.llm_task.*": {"queue": "llm"},
}

app.autodiscover_tasks(["ai_worker.task"])

if __name__ == "__main__":
    app.start()
