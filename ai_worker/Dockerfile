FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --group ai --no-dev --frozen

COPY ./ai_worker ./ai_worker

CMD ["uv", "run", "python", "-m", "celery", "-A", "ai_worker.main", "worker", "--loglevel=info", "-Q", "llm, image"]
