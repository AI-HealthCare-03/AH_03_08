# app/tests/image_apis/test_image_apis.py
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

_SIGNUP = {
    "email": "image_test@example.com",
    "password": "Password123!",
    "name": "이미지테스터",
    "gender": "MALE",
    "birth_date": "1995-05-20",
    "phone_number": "01012345678",
}
_LOGIN = {"email": "image_test@example.com", "password": "Password123!"}


async def _get_auth_headers(client: AsyncClient) -> dict:
    await client.post("/api/v1/auth/signup", json=_SIGNUP)
    resp = await client.post("/api/v1/auth/login", json=_LOGIN)
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


class TestAnalyzeImageAPI(TestCase):
    async def test_analyze_success(self):
        """정상적인 낱알약 분류 요청 테스트"""
        with patch("app.services.image.celery_app.send_task") as mock_task:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = await _get_auth_headers(client)
                response = await client.post(
                    "/api/v1/images/analyze",
                    headers=headers,
                    data={"record_id": "00000000-0000-0000-0000-000000000001"},
                )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "analysis_id" in data
        assert data["status"] == "processing"
        mock_task.assert_called_once()

    async def test_analyze_unauthorized(self):
        """JWT 인증 없이 요청 시 401 반환 테스트"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/images/analyze",
                data={"record_id": "00000000-0000-0000-0000-000000000001"},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_analyze_missing_record_id(self):
        """record_id 없이 요청 시 422 반환 테스트"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            response = await client.post(
                "/api/v1/images/analyze",
                headers=headers,
                data={},
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetAnalysisResultAPI(TestCase):
    async def test_get_result_success(self):
        """분석 결과 조회 테스트"""
        with patch("app.services.image.celery_app.send_task"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = await _get_auth_headers(client)

                # 분석 요청 먼저
                analyze_resp = await client.post(
                    "/api/v1/images/analyze",
                    headers=headers,
                    data={"record_id": "00000000-0000-0000-0000-000000000001"},
                )
                analysis_id = analyze_resp.json()["analysis_id"]

                # 결과 조회
                response = await client.get(
                    f"/api/v1/images/{analysis_id}",
                    headers=headers,
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["analysis_id"] == analysis_id
        assert data["status"] == "processing"

    async def test_get_result_unauthorized(self):
        """JWT 인증 없이 결과 조회 시 401 반환 테스트"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/images/00000000-0000-0000-0000-000000000001",
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED