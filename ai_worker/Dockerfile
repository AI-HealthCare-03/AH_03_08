FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --group ai --no-dev --frozen

COPY ./ai_worker ./ai_worker
COPY ./data/rag ./data/rag
COPY ./scripts/ingest_chroma_knowledge.py ./scripts/ingest_chroma_knowledge.py

CMD ["uv", "run", "python", "-m", "celery", "-A", "ai_worker.main", "worker", "--loglevel=info", "-Q", "llm,image"]
