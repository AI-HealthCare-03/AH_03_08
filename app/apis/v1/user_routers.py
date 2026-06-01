from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user, require_admin
from app.dtos.users import UserInfoResponse, UserUpdateRequest
from app.models.users import User
from app.services import feedback_service
from app.services.users import UserManageService

user_router = APIRouter(prefix="/users", tags=["users"])
CurrentAdmin = Annotated[User, Depends(require_admin)]


def _ok(data, message: str) -> dict:
    return {"success": True, "data": data, "message": message}


@user_router.get("/admin", status_code=status.HTTP_200_OK)
async def list_feedbacks_admin(
    admin: CurrentAdmin,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    data = await feedback_service.list_admin_feedbacks(page=page, limit=limit)
    return _ok(data, "관리자 피드백 목록 조회 성공")


@user_router.get("/me", response_model=UserInfoResponse, status_code=status.HTTP_200_OK)
async def user_me_info(
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    return Response(UserInfoResponse.model_validate(user).model_dump(), status_code=status.HTTP_200_OK)


@user_router.patch("/me", response_model=UserInfoResponse, status_code=status.HTTP_200_OK)
async def update_user_me_info(
    update_data: UserUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    user_manage_service: Annotated[UserManageService, Depends(UserManageService)],
) -> Response:
    updated_user = await user_manage_service.update_user(user=user, data=update_data)
    return Response(UserInfoResponse.model_validate(updated_user).model_dump(), status_code=status.HTTP_200_OK)
