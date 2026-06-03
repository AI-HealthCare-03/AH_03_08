import re
from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase
from app.main import app


class TestJWTTokenRefreshAPI(TestCase):
    async def test_token_refresh_success(self):
        signup_data = {
            "email": "refresh@example.com",
            "password": "Password123!",
            "name": "refreshtest",
            "gender": "MALE",
            "birth_date": "1990-01-01",
            "phone_number": "01099998888",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)
            login_response = await client.post(
                "/api/v1/auth/login",
                json={"email": "refresh@example.com", "password": "Password123!"},
            )
            set_cookie = login_response.headers.get("set-cookie", "")
            match = re.search(r"refresh_token=([^;]+)", set_cookie)
            refresh_token = match.group(1) if match else ""
            client.cookies["refresh_token"] = refresh_token
            response = await client.get("/api/v1/auth/token/refresh")
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()["data"]

    async def test_token_refresh_missing_token(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/auth/token/refresh")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Refresh token is missing."