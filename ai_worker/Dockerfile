FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --group ai --no-dev --frozen

COPY ./ai_worker ./ai_worker
COPY ./data/rag ./data/rag
COPY ./scripts/ingest_chroma_knowledge.py ./scripts/ingest_chroma_knowledge.py

# docker-compose command가 -A ai_worker.celery_app 으로 override하므로
# CMD는 fallback용. celery_app으로 통일하여 main.py 혼용 제거.
CMD ["uv", "run", "--no-sync", "celery", "-A", "ai_worker.celery_app", "worker", "--loglevel=info"]