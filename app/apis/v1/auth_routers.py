from typing import Annotated

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from fastapi.responses import JSONResponse as Response

from app.core import config
from app.core.config import Env, config
from app.dtos.auth import GoogleLoginRequest, LoginRequest, LoginResponse, SignUpRequest, TokenRefreshResponse
from app.models.users import User
from app.services.auth import AuthService, GoogleAuthService
from app.services.jwt import JwtService

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignUpRequest,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> Response:
    await auth_service.signup(request)
    return Response(content={"detail": "회원가입이 성공적으로 완료되었습니다."}, status_code=status.HTTP_201_CREATED)


@auth_router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> Response:
    user = await auth_service.authenticate(request)
    tokens = await auth_service.login(user)
    resp = Response(
        content=LoginResponse(access_token=str(tokens["access_token"])).model_dump(), status_code=status.HTTP_200_OK
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


@auth_router.get("/token/refresh", response_model=TokenRefreshResponse, status_code=status.HTTP_200_OK)
async def token_refresh(
    jwt_service: Annotated[JwtService, Depends(JwtService)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> Response:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is missing.")
    access_token = jwt_service.refresh_jwt(refresh_token)
    return Response(
        content=TokenRefreshResponse(access_token=str(access_token)).model_dump(), status_code=status.HTTP_200_OK
    )




class GoogleAuthService:
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    def __init__(self):
        self.user_repo = UserRepository()
        self.jwt_service = JwtService()

    async def get_google_user_info(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                self.GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": config.GOOGLE_CLIENT_ID,
                    "client_secret": config.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": config.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            token_data = token_response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="구글 인증에 실패했습니다."
                )

            user_response = await client.get(
                self.GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return user_response.json()

    async def social_login(self, code: str) -> User:
        user_info = await self.get_google_user_info(code)

        google_id = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name", "")

        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="구글 유저 정보를 가져올 수 없습니다."
            )

        # 기존 OAuth 유저 조회
        user = await self.user_repo.get_user_by_oauth("google", google_id)

        if not user:
            user = await self.user_repo.get_user_by_email(email)
            if user:
                user.oauth_provider = "google"
                user.oauth_id = google_id
                await user.save(update_fields=["oauth_provider", "oauth_id"])
            else:
                user = await self.user_repo.create_oauth_user(
                    email=email,
                    name=name,
                    oauth_provider="google",
                    oauth_id=google_id,
                )

        return user

    async def login(self, user: User) -> dict:
        await self.user_repo.update_last_login(user.id)
        return self.jwt_service.issue_jwt_pair(user)
    
@auth_router.post("/google", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def google_login(
    request: GoogleLoginRequest,
) -> Response:
    """구글 소셜 로그인 - 인가 코드로 로그인/자동 회원가입"""
    google_service = GoogleAuthService()
    user = await google_service.social_login(request.code)
    tokens = await google_service.login(user)
    resp = Response(
        content=LoginResponse(access_token=str(tokens["access_token"])).model_dump(),
        status_code=status.HTTP_200_OK
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