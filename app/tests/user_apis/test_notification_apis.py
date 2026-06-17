from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

SIGNUP_DATA = {
    "email": "notif_test@example.com",
    "password": "Password123!",
    "name": "알림테스트",
    "gender": "FEMALE",
    "birth_date": "1992-03-15",
    "phone_number": "01055556666",
}
LOGIN_DATA = {"email": "notif_test@example.com", "password": "Password123!"}


async def _get_token(client):
    await client.post("/api/v1/auth/signup", json=SIGNUP_DATA)
    resp = await client.post("/api/v1/auth/login", json=LOGIN_DATA)
    return resp.json()["data"]["access_token"]


class TestNotificationAPI(TestCase):
    async def test_list_notifications_empty(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            resp = await c.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["data"] == []

    async def test_create_notification_invalid_medication(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            resp = await c.post(
                "/api/v1/notifications",
                json={
                    "medication_id": "00000000-0000-0000-0000-000000000000",
                    "title": "test",
                    "type": "push",
                    "scheduled_time": "08:00:00",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_toggle_notification_not_found(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            resp = await c.put(
                "/api/v1/notifications/00000000-0000-0000-0000-000000000000",
                json={"is_active": False},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_notification_not_found(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            resp = await c.delete(
                "/api/v1/notifications/00000000-0000-0000-0000-000000000000",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_notification_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get("/api/v1/notifications")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
