from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app
from app.models.guide import Guide
from app.models.medical_records import MedicalRecord
from app.models.users import User

_SIGNUP = {
    "email": "guide_gen_test@example.com",
    "password": "Password123!",
    "name": "가이드테스터",
    "gender": "FEMALE",
    "birth_date": "1995-05-20",
    "phone_number": "01077778888",
}
_LOGIN = {"email": "guide_gen_test@example.com", "password": "Password123!"}


async def _get_auth_headers(client: AsyncClient) -> dict:
    await client.post("/api/v1/auth/signup", json=_SIGNUP)
    resp = await client.post("/api/v1/auth/login", json=_LOGIN)
    return {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}


async def _user_and_record() -> tuple[User, MedicalRecord]:
    user = await User.get(email=_SIGNUP["email"])
    record = await MedicalRecord.create(
        user=user,
        record_type=0,
        status="DONE",
        parsed_data={"medications": [{"drug_name": "타이레놀", "dosage": "500mg"}]},
    )
    return user, record


class TestGuideGenerateAPI(TestCase):
    async def test_generate_guide_accepted(self):
        """POST /guides/generate → 202, Celery 큐 등록."""
        with patch("app.apis.v1.guide_routers.celery_app") as mock_celery:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = await _get_auth_headers(client)
                _, record = await _user_and_record()
                response = await client.post(
                    "/api/v1/guides/generate",
                    headers=headers,
                    json={"record_id": str(record.id)},
                )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()["data"]
        assert data["status"] == "processing"
        assert "guide_id" in data
        mock_celery.send_task.assert_called_once()

        guide = await Guide.get(id=data["guide_id"])
        assert guide.llm_temperature == 0.0

    async def test_generate_guide_returns_existing(self):
        """동일 record_id 재요청 시 기존 guide 반환, send_task 미호출."""
        with patch("app.apis.v1.guide_routers.celery_app") as mock_celery:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = await _get_auth_headers(client)
                user, record = await _user_and_record()
                existing = await Guide.create(
                    user_id=user.id,
                    record_id=record.id,
                    status="done",
                    llm_temperature=0.0,
                )
                response = await client.post(
                    "/api/v1/guides/generate",
                    headers=headers,
                    json={"record_id": str(record.id)},
                )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json()["data"]["guide_id"] == str(existing.id)
        mock_celery.send_task.assert_not_called()

    async def test_generate_guide_record_not_found(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            response = await client.post(
                "/api/v1/guides/generate",
                headers=headers,
                json={"record_id": "00000000-0000-0000-0000-000000000099"},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_guide_status_and_detail(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            user, record = await _user_and_record()
            guide = await Guide.create(
                user_id=user.id,
                record_id=record.id,
                status="done",
                llm_model="gpt-4o-mini",
                llm_temperature=0.0,
                medication_guide={"raw": "복용 안내"},
            )
            status_resp = await client.get(f"/api/v1/guides/{guide.id}/status", headers=headers)
            detail_resp = await client.get(f"/api/v1/guides/{guide.id}", headers=headers)

        assert status_resp.status_code == status.HTTP_200_OK
        assert status_resp.json()["data"]["status"] == "done"
        assert detail_resp.status_code == status.HTTP_200_OK
        assert detail_resp.json()["data"]["llm_temperature"] == 0.0

    async def test_generate_guide_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/guides/generate",
                json={"record_id": "00000000-0000-0000-0000-000000000001"},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
