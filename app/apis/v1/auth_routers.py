import secrets
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse as Response

from app.core.config import Env, config
from app.dtos.auth import (
    GoogleLoginRequest,
    KakaoLoginRequest,
    LoginRequest,
    LoginResponse,
    SignUpRequest,
    TokenRefreshResponse,
)
from app.dtos.base import BaseResponse
from app.models.users import User
from app.services.auth import AuthService, GoogleAuthService, KakaoAuthService
from app.services.email_service import EmailService
from app.services.jwt import JwtService

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignUpRequest,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> Response:
    await auth_service.signup(request)
    return Response(
        content=BaseResponse(success=True, data=None, message="Signup successful.").model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> Response:
    user = await auth_service.authenticate(request)
    tokens = await auth_service.login(user)
    resp = Response(
        content=BaseResponse(
            success=True,
            data=LoginResponse(access_token=str(tokens["access_token"])).model_dump(),
            message="Login successful.",
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )
    resp.set_cookie(
        key="refresh_token",
        value=str(tokens["refresh_token"]),
        httponly=True,
        secure=True if config.ENV == Env.PROD else False,
        domain=config.COOKIE_DOMAIN or None,
        expires=tokens["access_token"].payload["exp"],
    )
    return resp


@auth_router.get("/token/refresh", status_code=status.HTTP_200_OK)
async def token_refresh(
    jwt_service: Annotated[JwtService, Depends(JwtService)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> Response:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is missing.")
    access_token = jwt_service.refresh_jwt(refresh_token)
    return Response(
        content=BaseResponse(
            success=True,
            data=TokenRefreshResponse(access_token=str(access_token)).model_dump(),
            message="Token refreshed.",
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@auth_router.post("/verify-email/send", status_code=status.HTTP_200_OK)
async def send_verification_email(
    email: str = Query(...),
) -> Response:
    user = await User.get_or_none(email=email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")
    if user.is_email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 인증된 이메일입니다.")
    token = secrets.token_hex(32)
    user.email_verify_token = token
    await user.save(update_fields=["email_verify_token"])
    email_service = EmailService()
    await email_service.send_verification_email(to_email=email, token=token)
    return Response(
        content=BaseResponse(success=True, data=None, message="인증 메일이 발송되었습니다.").model_dump(),
        status_code=status.HTTP_200_OK,
    )


@auth_router.get("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(token: str = Query(...)) -> Response:
    user = await User.get_or_none(email_verify_token=token)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 인증 토큰입니다.")
    user.is_email_verified = True
    user.email_verify_token = None
    await user.save(update_fields=["is_email_verified", "email_verify_token"])
    return Response(
        content=BaseResponse(success=True, data=None, message="이메일 인증이 완료되었습니다.").model_dump(),
        status_code=status.HTTP_200_OK,
    )


@auth_router.post("/google", status_code=status.HTTP_200_OK)
async def google_login(
    request: GoogleLoginRequest,
) -> Response:
    google_service = GoogleAuthService()
    user = await google_service.social_login(request.code)
    tokens = await google_service.login(user)
    resp = Response(
        content=BaseResponse(
            success=True,
            data=LoginResponse(access_token=str(tokens["access_token"])).model_dump(),
            message="Google login successful.",
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )
    resp.set_cookie(
        key="refresh_token",
        value=str(tokens["refresh_token"]),
        httponly=True,
        secure=True if config.ENV == Env.PROD else False,
        domain=config.COOKIE_DOMAIN or None,
        expires=tokens["access_token"].payload["exp"],
    )
    return resp


@auth_router.post("/kakao", status_code=status.HTTP_200_OK)
async def kakao_login(
    request: KakaoLoginRequest,
) -> Response:
    kakao_service = KakaoAuthService()
    user = await kakao_service.social_login(request.code)
    tokens = await kakao_service.login(user)
    resp = Response(
        content=BaseResponse(
            success=True,
            data=LoginResponse(access_token=str(tokens["access_token"])).model_dump(),
            message="Kakao login successful.",
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )
    resp.set_cookie(
        key="refresh_token",
        value=str(tokens["refresh_token"]),
        httponly=True,
        secure=True if config.ENV == Env.PROD else False,
        domain=config.COOKIE_DOMAIN or None,
        expires=tokens["access_token"].payload["exp"],
    )
    return resp