import os

from celery import Celery

app = Celery(
    "ai_worker",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
)

app.conf.task_routes = {
    "ai_worker.tasks.llm_tasks.*": {"queue": "llm"},
    "ai_worker.tasks.llm_task.generate_guide": {"queue": "llm"},
}

app.autodiscover_tasks(["ai_worker.tasks"])

if __name__ == "__main__":
    app.start()
