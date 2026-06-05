from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

SIGNUP_DATA = {
    "email": "health_test@example.com",
    "password": "Password123!",
    "name": "healthtest",
    "gender": "MALE",
    "birth_date": "1990-01-01",
    "phone_number": "01033334444",
}
LOGIN_DATA = {"email": "health_test@example.com", "password": "Password123!"}


async def _get_token(client):
    await client.post("/api/v1/auth/signup", json=SIGNUP_DATA)
    resp = await client.post("/api/v1/auth/login", json=LOGIN_DATA)
    return resp.json()["data"]["access_token"]


class TestUserMeAPI(TestCase):
    async def test_get_my_profile(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            resp = await c.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["data"]["email"] == SIGNUP_DATA["email"]

    async def test_update_my_profile(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            resp = await c.patch(
                "/api/v1/users/me",
                json={"name": "updated", "height_cm": 175.0, "weight_kg": 70.0},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["success"] is True

    async def test_get_profile_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get("/api/v1/users/me")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestAllergyAPI(TestCase):
    async def test_allergy_crud(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            headers = {"Authorization": f"Bearer {token}"}
            resp = await c.get("/api/v1/users/me/allergies", headers=headers)
            assert resp.status_code == status.HTTP_200_OK
            assert resp.json()["data"] == []
            resp = await c.post(
                "/api/v1/users/me/allergies",
                json={"allergen_name": "penicillin", "severity": "severe"},
                headers=headers,
            )
            assert resp.status_code == status.HTTP_201_CREATED
            allergy_id = resp.json()["data"]["id"]
            resp = await c.get("/api/v1/users/me/allergies", headers=headers)
            assert len(resp.json()["data"]) == 1
            resp = await c.delete(f"/api/v1/users/me/allergies/{allergy_id}", headers=headers)
            assert resp.status_code == status.HTTP_200_OK
            resp = await c.get("/api/v1/users/me/allergies", headers=headers)
            assert resp.json()["data"] == []

    async def test_allergy_delete_not_found(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            resp = await c.delete(
                "/api/v1/users/me/allergies/00000000-0000-0000-0000-000000000000",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_allergy_invalid_severity(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            resp = await c.post(
                "/api/v1/users/me/allergies",
                json={"allergen_name": "aspirin", "severity": "invalid"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestConditionAPI(TestCase):
    async def test_condition_crud(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            headers = {"Authorization": f"Bearer {token}"}
            resp = await c.get("/api/v1/users/me/conditions", headers=headers)
            assert resp.status_code == status.HTTP_200_OK
            assert resp.json()["data"] == []
            resp = await c.post(
                "/api/v1/users/me/conditions",
                json={"condition_name": "hypertension", "severity": "moderate"},
                headers=headers,
            )
            assert resp.status_code == status.HTTP_201_CREATED
            condition_id = resp.json()["data"]["id"]
            resp = await c.get("/api/v1/users/me/conditions", headers=headers)
            assert len(resp.json()["data"]) == 1
            resp = await c.delete(f"/api/v1/users/me/conditions/{condition_id}", headers=headers)
            assert resp.status_code == status.HTTP_200_OK
            resp = await c.get("/api/v1/users/me/conditions", headers=headers)
            assert resp.json()["data"] == []

    async def test_condition_delete_not_found(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            token = await _get_token(c)
            resp = await c.delete(
                "/api/v1/users/me/conditions/00000000-0000-0000-0000-000000000000",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
