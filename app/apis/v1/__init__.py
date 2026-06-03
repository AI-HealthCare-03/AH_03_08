from fastapi import APIRouter

from app.apis.v1.ai_routers import ai_router
from app.apis.v1.asset_routers import asset_router
from app.apis.v1.auth_routers import auth_router
from app.apis.v1.feedback_routers import feedback_router
from app.apis.v1.guide_routers import guide_router
from app.apis.v1.health_routers import health_router
from app.apis.v1.image_routers import image_router
from app.apis.v1.internal_routers import internal_router
from app.apis.v1.llm_routers import chat_router
from app.apis.v1.user_routers import user_router
from app.presentation.api.v1.chats.router import chats_router
from app.presentation.api.v1.records.router import records_router
from app.apis.v1.notification_routers import notification_router
from app.apis.v1.calendar_routers import calendar_router

v1_routers = APIRouter(prefix="/api/v1")
v1_routers.include_router(auth_router)
v1_routers.include_router(user_router)
v1_routers.include_router(health_router)
# UUID 기반 records API가 llm record_router(int)보다 먼저 매칭되도록 순서 유지
v1_routers.include_router(records_router)
# v1_routers.include_router(record_router)
v1_routers.include_router(asset_router)
v1_routers.include_router(guide_router)
# v1_routers.include_router(chat_router)
v1_routers.include_router(chats_router)
v1_routers.include_router(image_router)
v1_routers.include_router(ai_router)
v1_routers.include_router(feedback_router)
v1_routers.include_router(internal_router)  # Worker 콜백 + SSE
v1_routers.include_router(notification_router)
v1_routers.include_router(calendar_router)
