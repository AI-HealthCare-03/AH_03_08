import pytest
from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase
from app.main import app


class TestKakaoAuthAPI(TestCase):
    async def test_kakao_login_invalid_code(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post("/api/v1/auth/kakao", json={"code": "invalid_code"})
        assert resp.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @pytest.mark.skip(reason="Kakao OAuth 외부 API 미연동 - AWS 배포 후 구현")
    async def test_kakao_login_mock_success(self):
        pass

    async def test_kakao_login_missing_code(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post("/api/v1/auth/kakao", json={})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY