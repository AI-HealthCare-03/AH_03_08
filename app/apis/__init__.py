from fastapi import APIRouter

from app.apis.v1.auth_routers import auth_router
from app.apis.v1.llm_routers import guide_router
from app.apis.v1.user_routers import user_router
from app.presentation.api.v1.chats.router import chats_router
from app.presentation.api.v1.records.router import records_router

v1_routers = APIRouter(prefix="/api/v1")
v1_routers.include_router(auth_router)
v1_routers.include_router(user_router)
v1_routers.include_router(records_router)
v1_routers.include_router(guide_router)
v1_routers.include_router(chats_router)