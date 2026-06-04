from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

_SIGNUP = {
    "email": "tts_test@example.com",
    "password": "Password123!",
    "name": "TTS테스터",
    "gender": "MALE",
    "birth_date": "1995-05-20",
    "phone_number": "01098765432",
}
_LOGIN = {"email": "tts_test@example.com", "password": "Password123!"}


async def _get_auth_headers(client: AsyncClient) -> dict:
    await client.post("/api/v1/auth/signup", json=_SIGNUP)
    resp = await client.post("/api/v1/auth/login", json=_LOGIN)
    return {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}


def _mock_guide():
    guide = MagicMock()
    guide.summary_text = "테스트 요약 텍스트입니다."
    return guide


class TestCreateGuideAssetAPI(TestCase):
    async def test_create_tts_success(self):
        """tts 타입 TTS 생성 요청 테스트"""
        with (
            patch("app.apis.v1.asset_routers.Guide.get_or_none", new=AsyncMock(return_value=_mock_guide())),
            patch("app.services.tts.TtsService.create_tts_asset", new=AsyncMock(return_value=b"mock_audio")),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = await _get_auth_headers(client)
                response = await client.post(
                    "/api/v1/guides/00000000-0000-0000-0000-000000000001/assets",
                    headers=headers,
                    json={"asset_type": "tts"},
                )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "audio/mpeg"

    async def test_create_invalid_asset_type(self):
        """잘못된 asset_type 요청 시 422 반환 테스트"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            response = await client.post(
                "/api/v1/guides/00000000-0000-0000-0000-000000000001/assets",
                headers=headers,
                json={"asset_type": "invalid_type"},
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_unauthorized(self):
        """JWT 인증 없이 요청 시 401 반환 테스트"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/guides/00000000-0000-0000-0000-000000000001/assets",
                json={"asset_type": "tts"},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_create_missing_asset_type(self):
        """asset_type 없이 요청 시 422 반환 테스트"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            response = await client.post(
                "/api/v1/guides/00000000-0000-0000-0000-000000000001/assets",
                headers=headers,
                json={},
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY