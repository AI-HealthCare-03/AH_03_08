import os
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

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


app = FastAPI(
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
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

app.include_router(v1_routers)
