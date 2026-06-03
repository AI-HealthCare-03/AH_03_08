import httpx
from fastapi.exceptions import HTTPException
from pydantic import EmailStr
from starlette import status
from tortoise.transactions import in_transaction

from app.core.config import config
from app.core.jwt.tokens import AccessToken, RefreshToken
from app.core.utils.common import normalize_phone_number
from app.core.utils.security import hash_password, verify_password
from app.dtos.auth import LoginRequest, SignUpRequest
from app.models.users import User
from app.repositories.user_repository import UserRepository
from app.services.jwt import JwtService


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.jwt_service = JwtService()

    async def signup(self, data: SignUpRequest) -> User:
        await self.check_email_exists(data.email)
        normalized_phone_number = normalize_phone_number(data.phone_number)
        await self.check_phone_number_exists(normalized_phone_number)
        async with in_transaction():
            user = await self.user_repo.create_user(
                email=data.email,
                hashed_password=hash_password(data.password),
                name=data.name,
                phone_number=normalized_phone_number,
                gender=data.gender,
                birth_date=data.birth_date,
            )
            return user

    async def authenticate(self, data: LoginRequest) -> User:
        email = str(data.email)
        user = await self.user_repo.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="?대찓???먮뒗 鍮꾨?踰덊샇媛 ?щ컮瑜댁? ?딆뒿?덈떎."
            )
        if not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="?대찓???먮뒗 鍮꾨?踰덊샇媛 ?щ컮瑜댁? ?딆뒿?덈떎."
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="鍮꾪솢?깊솕??怨꾩젙?낅땲??")
        return user

    async def login(self, user: User) -> dict[str, AccessToken | RefreshToken]:
        await self.user_repo.update_last_login(user.id)
        return self.jwt_service.issue_jwt_pair(user)

    async def check_email_exists(self, email: str | EmailStr) -> None:
        if await self.user_repo.exists_by_email(email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="?대? ?ъ슜以묒씤 ?대찓?쇱엯?덈떎.")

    async def check_phone_number_exists(self, phone_number: str) -> None:
        if await self.user_repo.exists_by_phone_number(phone_number):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="?대? ?ъ슜以묒씤 ?대???踰덊샇?낅땲??")


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
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="援ш? ?몄쬆???ㅽ뙣?덉뒿?덈떎.")

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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="援ш? ?좎? ?뺣낫瑜?媛?몄삱 ???놁뒿?덈떎.")

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


class KakaoAuthService:
    KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    KAKAO_USERINFO_URL = "https://kapi.kakao.com/v2/user/me"

    def __init__(self):
        self.user_repo = UserRepository()
        self.jwt_service = JwtService()

    async def get_kakao_user_info(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                self.KAKAO_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": config.KAKAO_CLIENT_ID,
                    "client_secret": config.KAKAO_CLIENT_SECRET,
                    "redirect_uri": config.KAKAO_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            token_data = token_response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kakao token exchange failed.")

            user_response = await client.get(
                self.KAKAO_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return user_response.json()

    async def social_login(self, code: str) -> User:
        user_info = await self.get_kakao_user_info(code)

        kakao_id = str(user_info.get("id", ""))
        kakao_account = user_info.get("kakao_account", {})
        email = kakao_account.get("email", f"kakao_{kakao_id}@medilog.internal")
        name = kakao_account.get("profile", {}).get("nickname", f"kakao_{kakao_id[:6]}")

        if not kakao_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to retrieve Kakao user info.")

        user = await self.user_repo.get_user_by_oauth("kakao", kakao_id)

        if not user:
            user = await self.user_repo.get_user_by_email(email)
            if user:
                user.oauth_provider = "kakao"
                user.oauth_id = kakao_id
                await user.save(update_fields=["oauth_provider", "oauth_id"])
            else:
                user = await self.user_repo.create_oauth_user(
                    email=email,
                    name=name,
                    oauth_provider="kakao",
                    oauth_id=kakao_id,
                )

        return user

    async def login(self, user: User) -> dict:
        await self.user_repo.update_last_login(user.id)
        return self.jwt_service.issue_jwt_pair(user)