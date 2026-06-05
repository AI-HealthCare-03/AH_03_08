from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

_SIGNUP = {
    "email": "card_news_test@example.com",
    "password": "Password123!",
    "name": "카드뉴스테스터",
    "gender": "MALE",
    "birth_date": "1995-05-20",
    "phone_number": "01011112222",
}
_LOGIN = {"email": "card_news_test@example.com", "password": "Password123!"}


async def _get_auth_headers(client: AsyncClient) -> dict:
    await client.post("/api/v1/auth/signup", json=_SIGNUP)
    resp = await client.post("/api/v1/auth/login", json=_LOGIN)
    return {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}


def _mock_guide():
    guide = MagicMock()
    guide.summary_text = "테스트 요약 텍스트입니다."
    return guide


class TestCreateCardNewsAPI(TestCase):
    async def test_create_card_news_success(self):
        """card_news 타입 카드뉴스 생성 요청 테스트"""
        with (
            patch("app.apis.v1.asset_routers.Guide.get_or_none", new=AsyncMock(return_value=_mock_guide())),
            patch("app.services.card_news.CardNewsService.create_card_news_asset", new=AsyncMock(return_value=b"mock_image")),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = await _get_auth_headers(client)
                response = await client.post(
                    "/api/v1/guides/00000000-0000-0000-0000-000000000001/assets",
                    headers=headers,
                    json={"asset_type": "card_news"},
                )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "image/png"

    async def test_create_card_news_guide_not_found(self):
        """존재하지 않는 guide_id로 요청 시 404 반환 테스트"""
        with patch("app.apis.v1.asset_routers.Guide.get_or_none", new=AsyncMock(return_value=None)):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = await _get_auth_headers(client)
                response = await client.post(
                    "/api/v1/guides/00000000-0000-0000-0000-000000000099/assets",
                    headers=headers,
                    json={"asset_type": "card_news"},
                )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_card_news_unauthorized(self):
        """JWT 인증 없이 요청 시 401 반환 테스트"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/guides/00000000-0000-0000-0000-000000000001/assets",
                json={"asset_type": "card_news"},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED