"""Celery CLI 진입점 — docker-compose와 동일하게 celery_app만 사용."""

from ai_worker.celery_app import celery_app

app = celery_app

__all__ = ["app", "celery_app"]
