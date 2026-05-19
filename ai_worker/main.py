from celery import Celery
import os

app = Celery(
    'ai_worker',
    broker=os.getenv('REDIS_URL', 'redis://redis:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://redis:6379/0'),
)

app.conf.task_routes = {
    'ai_worker.tasks.llm_task.*': {'queue': 'llm'},
}

app.autodiscover_tasks(['ai_worker.tasks'])

if __name__ == '__main__':
    app.start()
