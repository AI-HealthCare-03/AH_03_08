from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase
from app.main import app


class TestSignupAPI(TestCase):
    async def test_signup_success(self):
        signup_data = {
            "email": "test@example.com",
            "email_token": "valid_test_token",
            "password": "Password123!",
            "name": "testuser",
            "gender": "MALE",
            "birth_date": "1990-01-01",
            "phone_number": "01012345678",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Redis mock: email_token 검증 통과
            with patch("app.apis.v1.auth_routers.Request") as mock_req:
                mock_redis = AsyncMock()
                mock_redis.get = AsyncMock(return_value="test@example.com")
                mock_redis.delete = AsyncMock()
                mock_req.return_value.app.state.redis = mock_redis
                response = await client.post("/api/v1/auth/signup", json=signup_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["success"] is True

    async def test_signup_invalid_email(self):
        signup_data = {
            "email": "invalid-email",
            "email_token": "token",
            "password": "password123!",
            "name": "testuser",
            "gender": "MALE",
            "birth_date": "1990-01-01",
            "phone_number": "01012345678",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/auth/signup", json=signup_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY