from fastapi import APIRouter

from app.apis.v1.admin_routers import router as admin_router
from app.apis.v1.ai_routers import ai_router
from app.apis.v1.auth_routers import auth_router
from app.apis.v1.guide_routers import router as guide_router
from app.apis.v1.health_routers import health_router
from app.apis.v1.image_routers import image_router
from app.apis.v1.llm_routers import chat_router, record_router
from app.apis.v1.user_routers import user_router

v1_routers = APIRouter(prefix="/api/v1")
v1_routers.include_router(auth_router)
v1_routers.include_router(user_router)
v1_routers.include_router(health_router)
v1_routers.include_router(ai_router)
v1_routers.include_router(admin_router)
v1_routers.include_router(record_router)
v1_routers.include_router(guide_router)
v1_routers.include_router(image_router)
v1_routers.include_router(chat_router)
