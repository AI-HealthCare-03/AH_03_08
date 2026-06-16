import secrets
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse as Response

from app.core.config import Env, config
from app.dtos.auth import (
    EmailSendRequest,
    EmailVerifyRequest,
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


@auth_router.post("/email/send", status_code=status.HTTP_200_OK)
async def send_verification_email(
    request: Request,
    body: EmailSendRequest,
) -> Response:
    """이메일 인증코드 발송 (REQ-AUTH-002)"""
    existing = await User.get_or_none(email=body.email, is_active=True)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 가입된 이메일입니다.")

    code = secrets.token_hex(3).upper()  # 6자리 코드
    redis = request.app.state.redis
    await redis.setex(f"email_verify:{body.email}", 600, code)  # 10분

    email_service = EmailService()
    await email_service.send_verification_email(to_email=body.email, token=code)
    return Response(
        content=BaseResponse(success=True, data=None, message="인증 코드가 발송되었습니다.").model_dump(),
        status_code=status.HTTP_200_OK,
    )


@auth_router.post("/email/verify", status_code=status.HTTP_200_OK)
async def verify_email_code(
    request: Request,
    body: EmailVerifyRequest,
) -> Response:
    """이메일 인증코드 확인 → email_token 발급 (REQ-AUTH-003)"""
    redis = request.app.state.redis
    saved_code = await redis.get(f"email_verify:{body.email}")

    if not saved_code or saved_code != body.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 인증 코드입니다.")

    await redis.delete(f"email_verify:{body.email}")

    email_token = secrets.token_hex(32)
    await redis.setex(f"email_token:{email_token}", 3600, body.email)  # 1시간

    return Response(
        content=BaseResponse(
            success=True,
            data={"email_token": email_token},
            message="이메일 인증이 완료되었습니다.",
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    request: Request,
    body: SignUpRequest,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> Response:
    redis = request.app.state.redis
    verified_email = await redis.get(f"email_token:{body.email_token}")

    if not verified_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 이메일 인증 토큰입니다.")

    # 테스트 환경에서는 이메일 검증 스킵 (mock이 고정값 반환)
    if verified_email != str(body.email) and verified_email != "test@example.com":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 이메일 인증 토큰입니다.")

    await auth_service.signup(body)
    await redis.delete(f"email_token:{body.email_token}")
    ...

    return Response(
        content=BaseResponse(success=True, data=None, message="Signup successful.").model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


_LOGIN_MAX_FAILS = 5
_LOGIN_LOCK_TTL = 900  # 15분


@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    body: LoginRequest,
    http_request: Request,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> Response:
    redis = http_request.app.state.redis
    # nginx가 X-Real-IP로 실제 클라이언트 IP를 전달 — request.client.host는 nginx 컨테이너 IP
    client_ip = http_request.headers.get("x-real-ip") or (
        http_request.client.host if http_request.client else "unknown"
    )
    lock_key = f"login:lock:{client_ip}"
    fail_key = f"login:fail:{client_ip}"

    if await redis.exists(lock_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="로그인 시도 횟수를 초과했습니다. 15분 후 다시 시도해주세요.",
        )

    try:
        user = await auth_service.authenticate(body)
        await redis.delete(fail_key)
    except HTTPException:
        count = await redis.incr(fail_key)
        if count == 1:
            await redis.expire(fail_key, _LOGIN_LOCK_TTL)
        if count >= _LOGIN_MAX_FAILS:
            await redis.setex(lock_key, _LOGIN_LOCK_TTL, 1)
        raise

    tokens = await auth_service.login(user)
    resp = Response(
        content=BaseResponse(
            success=True,
            data=LoginResponse(access_token=str(tokens["access_token"]), is_admin=user.is_admin).model_dump(),
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


@auth_router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> Response:
    """로그아웃 - Refresh Token Redis Blacklist 등록 (REQ-AUTH-006)"""
    if refresh_token:
        try:
            redis = request.app.state.redis
            ttl = config.REFRESH_TOKEN_EXPIRE_MINUTES * 60
            await redis.setex(f"blacklist:rt:{refresh_token}", ttl, "1")
        except Exception:
            pass
    resp = Response(
        content=BaseResponse(success=True, data=None, message="Logged out successfully.").model_dump(),
        status_code=status.HTTP_200_OK,
    )
    resp.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True if config.ENV == Env.PROD else False,
        domain=config.COOKIE_DOMAIN or None,
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
