from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase
from app.main import app

SIGNUP_DATA = {
    "email": "calendar_test@example.com",
    "password": "Password123!",
    "name": "calendartest",
    "gender": "MALE",
    "birth_date": "1988-07-20",
    "phone_number": "01077778888",
}
LOGIN_DATA = {"email": "calendar_test@example.com", "password": "Password123!"}


async def _get_token(client):
    await client.post("/api/v1/auth/signup", json=SIGNUP_DATA)
    resp = await client.post("/api/v1/auth/login", json=LOGIN_DATA)
    return resp.json()["data"]["access_token"]


class TestCalendarAPI(TestCase):
    async def test_list_calendar_month_empty(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            resp = await c.get(
                "/api/v1/calendars?year=2026&month=6",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()["data"]
        assert body["year"] == 2026
        assert body["month"] == 6
        assert body["total"] == 0
        assert body["items"] == []

    async def test_list_calendar_by_date_empty(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            resp = await c.get("/api/v1/calendars/2026-06-01", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["data"] == []

    async def test_create_calendar_invalid_medication(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            resp = await c.post(
                "/api/v1/calendars",
                json={"medication_id": "00000000-0000-0000-0000-000000000000", "event_date": "2026-06-15", "scheduled_time": "09:00:00"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_calendar_status_not_found(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            resp = await c.put(
                "/api/v1/calendars/00000000-0000-0000-0000-000000000000/status",
                json={"status": "TAKEN"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_calendar_not_found(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            resp = await c.delete(
                "/api/v1/calendars/00000000-0000-0000-0000-000000000000",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_calendar_invalid_status_value(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            resp = await c.put(
                "/api/v1/calendars/00000000-0000-0000-0000-000000000000/status",
                json={"status": "COMPLETED"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_calendar_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get("/api/v1/calendars?year=2026&month=6")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED