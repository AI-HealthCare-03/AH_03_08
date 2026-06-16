from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app


class TestUserMeApis(TestCase):
    async def test_get_user_me_success(self):
        email = "me@example.com"
        signup_data = {
            "email": email,
            "email_token": email,
            "password": "Password123!",
            "name": "테스트유저",
            "gender": "FEMALE",
            "birth_date": "1992-02-02",
            "phone_number": "01055556666",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)
            login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
            access_token = login_response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["email"] == email

    async def test_update_user_me_success(self):
        email = "update_me@example.com"
        signup_data = {
            "email": email,
            "email_token": email,
            "password": "Password123!",
            "name": "수정전",
            "gender": "MALE",
            "birth_date": "1990-10-10",
            "phone_number": "01077778888",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)
            login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
            access_token = login_response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.patch("/api/v1/users/me", json={"name": "수정후"}, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True

    async def test_get_user_me_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
