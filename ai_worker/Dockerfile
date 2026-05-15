FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --group ai --no-dev

RUN uv pip install celery redis --python /app/.venv/bin/python

COPY ./ai_worker ./ai_worker

CMD ["/app/.venv/bin/celery", "-A", "ai_worker.main:celery_app", "worker", "--loglevel=info", "--concurrency=2"]