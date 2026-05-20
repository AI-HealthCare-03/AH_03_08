FROM python:3.13-slim

WORKDIR /app

# asyncmy==0.2.11 은 Apple Silicon(aarch64) 환경에서 prebuilt wheel 이 없어 소스 컴파일이 필요함
# gcc, libc6-dev 없으면 "error: command 'gcc' failed" 로 빌드 실패 (x86_64 환경에서는 무해)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --group ai --no-dev

RUN uv pip install celery redis --python /app/.venv/bin/python

COPY ./ai_worker ./ai_worker

CMD ["/app/.venv/bin/celery", "-A", "ai_worker.main:celery_app", "worker", "--loglevel=info", "--concurrency=2"]