from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from typing import Annotated
from fastapi.responses import JSONResponse as Response
from app.core.config import Env, config
from app.dtos.auth import GoogleLoginRequest, KakaoLoginRequest, LoginRequest, LoginResponse, SignUpRequest, TokenRefreshResponse
from app.dtos.base import BaseResponse
from app.services.auth import AuthService, GoogleAuthService, KakaoAuthService
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

@auth_router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    jwt_service: Annotated[JwtService, Depends(JwtService)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> Response:
    if refresh_token:
        try:
            verified = jwt_service.verify_jwt(refresh_token, token_type="refresh")
            exp = verified.payload.get("exp", 0)
            ttl = max(int(exp - __import__("time").time()), 0)
            if ttl > 0:
                redis = request.app.state.redis
                await redis.setex(f"blacklist:{refresh_token}", ttl, "1")
        except HTTPException:
            pass  # 이미 만료된 토큰은 무시

    resp = Response(
        content=BaseResponse(success=True, data=None, message="Logout successful.").model_dump(),
        status_code=status.HTTP_200_OK,
    )
    resp.delete_cookie(key="refresh_token")
    return resp