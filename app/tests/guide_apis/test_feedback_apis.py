from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app
from app.models.guide import Guide
from app.models.medical_records import MedicalRecord
from app.models.model_metrics import MetricSnapshot
from app.models.users import User

_SIGNUP = {
    "email": "feedback_test@example.com",
    "password": "Password123!",
    "name": "피드백테스터",
    "gender": "MALE",
    "birth_date": "1995-06-10",
    "phone_number": "01099990000",
}
_LOGIN = {"email": "feedback_test@example.com", "password": "Password123!"}


async def _get_auth_headers(client: AsyncClient) -> dict:
    await client.post("/api/v1/auth/signup", json=_SIGNUP)
    resp = await client.post("/api/v1/auth/login", json=_LOGIN)
    return {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}


async def _done_guide() -> Guide:
    user = await User.get(email=_SIGNUP["email"])
    record = await MedicalRecord.create(user=user, record_type=0, status="DONE")
    return await Guide.create(
        user_id=user.id,
        record_id=record.id,
        status="done",
        prompt_version="v1.0",
        llm_temperature=0.0,
    )


class TestFeedbackAPI(TestCase):
    async def test_submit_and_list_feedback(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            guide = await _done_guide()
            payload = {
                "guide_id": str(guide.id),
                "rating": 0,
                "tag_ids": ["negative_test_tag"],
                "comment": "pytest feedback",
            }
            post_resp = await client.post("/api/v1/guides/feedbacks", headers=headers, json=payload)
            list_resp = await client.get("/api/v1/guides/feedbacks/list", headers=headers)

        assert post_resp.status_code == status.HTTP_200_OK
        assert "feedback_id" in post_resp.json()["data"]

        assert list_resp.status_code == status.HTTP_200_OK
        items = list_resp.json()["data"]["items"]
        assert any(it["guide_id"] == str(guide.id) and it["comment"] == "pytest feedback" for it in items)

        snapshot = await MetricSnapshot.get_or_none(model_type="v1.0")
        assert snapshot is not None
        assert snapshot.total_count >= 1

    async def test_submit_feedback_guide_not_found(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            response = await client.post(
                "/api/v1/guides/feedbacks",
                headers=headers,
                json={
                    "guide_id": "00000000-0000-0000-0000-000000000099",
                    "rating": 1,
                    "comment": "missing guide",
                },
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_feedback_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/guides/feedbacks/list")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
