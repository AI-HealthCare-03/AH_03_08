import os
from contextlib import asynccontextmanager
from pathlib import Path

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from app.apis.v1 import v1_routers
from app.core.config import config
from app.core.db.databases import initialize_tortoise


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_url = getattr(config, "REDIS_URL", None) or os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    app.state.redis = aioredis.from_url(
        redis_url,
        decode_responses=True,
        max_connections=20,
    )
    yield
    await app.state.redis.aclose()


# 프로덕션 환경에서 Swagger UI 및 OpenAPI 스펙 노출 차단
_is_local = config.ENV == "local"
app = FastAPI(
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url="/api/docs" if _is_local else None,
    redoc_url="/api/redoc" if _is_local else None,
    openapi_url="/api/openapi.json" if _is_local else None,
)

# CORS — config에 get_allowed_origins가 있으면 사용, 없으면 기본값
_allowed_origins = config.get_allowed_origins() if callable(getattr(config, "get_allowed_origins", None)) else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

initialize_tortoise(app)

upload_dir = Path(config.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

app.include_router(v1_routers)
