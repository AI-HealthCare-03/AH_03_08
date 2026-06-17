# app/tests/image_apis/test_image_apis.py
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
    return {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}


class TestGetAnalysisResultAPI(TestCase):
    async def test_get_result_success(self):
        """분석 결과 조회 테스트"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)

            from app.models.medical_records import MedicalRecord
            from app.models.users import User

            user = await User.get(email="image_test@example.com")
            record = await MedicalRecord.create(
                user=user,
                record_type=2,
                status="PENDING",
            )

            response = await client.get(
                f"/api/v1/images/{record.id}",
                headers=headers,
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["record_id"] == str(record.id)
        assert data["status"] == "PENDING"

    async def test_get_result_unauthorized(self):
        """JWT 인증 없이 결과 조회 시 401 반환 테스트"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/images/00000000-0000-0000-0000-000000000001",
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
