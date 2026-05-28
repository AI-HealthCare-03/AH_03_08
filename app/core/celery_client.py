import os

from celery import Celery

_broker = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

celery_client = Celery(broker=_broker, backend=_backend)
