from ai_worker.celery_app import celery_app as app  # noqa: F401 — Celery가 'app' 이름으로 탐색
 
__all__ = ["app"]
