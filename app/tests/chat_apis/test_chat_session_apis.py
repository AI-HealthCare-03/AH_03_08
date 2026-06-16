from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

_SIGNUP = {
    "email": "chat_test@example.com",
    "email_token": "chat_test@example.com",
    "password": "Password123!",
    "name": "챗테스터",
    "gender": "MALE",
    "birth_date": "1990-01-01",
    "phone_number": "01011112222",
}
_LOGIN = {"email": "chat_test@example.com", "password": "Password123!"}


async def _get_auth_headers(client: AsyncClient) -> dict:
    await client.post("/api/v1/auth/signup", json=_SIGNUP)
    resp = await client.post("/api/v1/auth/login", json=_LOGIN)
    return {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}


class TestCreateSessionAPI(TestCase):
    async def test_create_session_success(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            response = await client.post("/api/v1/chats", headers=headers, json={})

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["title"] is None
        assert data["guide_id"] is None

    async def test_create_session_with_title(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            response = await client.post("/api/v1/chats", headers=headers, json={"title": "복약 문의"})

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["title"] == "복약 문의"

    async def test_create_session_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/chats", json={})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestListSessionsAPI(TestCase):
    async def test_list_sessions_success(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)

            for _ in range(3):
                await client.post("/api/v1/chats", headers=headers, json={})

            response = await client.get("/api/v1/chats", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["page"] == 1

    async def test_list_sessions_pagination(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)

            for _ in range(5):
                await client.post("/api/v1/chats", headers=headers, json={})

            response = await client.get("/api/v1/chats?page=1&limit=2", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    async def test_list_sessions_only_own(self):
        other_signup = {**_SIGNUP, "email": "chat_other@example.com", "phone_number": "01033334444"}
        other_login = {"email": "chat_other@example.com", "password": "Password123!"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers_a = await _get_auth_headers(client)
            await client.post("/api/v1/chats", headers=headers_a, json={})

            await client.post("/api/v1/auth/signup", json=other_signup)
            login_resp = await client.post("/api/v1/auth/login", json=other_login)
            headers_b = {"Authorization": f"Bearer {login_resp.json()['data']['access_token']}"}

            response = await client.get("/api/v1/chats", headers=headers_b)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 0


class TestGetSessionAPI(TestCase):
    async def test_get_session_success(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            create_resp = await client.post("/api/v1/chats", headers=headers, json={"title": "조회 테스트"})
            session_id = create_resp.json()["id"]

            response = await client.get(f"/api/v1/chats/{session_id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == session_id
        assert response.json()["title"] == "조회 테스트"

    async def test_get_session_not_found(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            response = await client.get(
                "/api/v1/chats/00000000-0000-0000-0000-000000000000",
                headers=headers,
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_session_other_user_not_found(self):
        other_signup = {**_SIGNUP, "email": "chat_other2@example.com", "phone_number": "01055556666"}
        other_login = {"email": "chat_other2@example.com", "password": "Password123!"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers_a = await _get_auth_headers(client)
            create_resp = await client.post("/api/v1/chats", headers=headers_a, json={})
            session_id = create_resp.json()["id"]

            await client.post("/api/v1/auth/signup", json=other_signup)
            login_resp = await client.post("/api/v1/auth/login", json=other_login)
            headers_b = {"Authorization": f"Bearer {login_resp.json()['data']['access_token']}"}
            response = await client.get(f"/api/v1/chats/{session_id}", headers=headers_b)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteSessionAPI(TestCase):
    async def test_delete_session_success(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            create_resp = await client.post("/api/v1/chats", headers=headers, json={})
            session_id = create_resp.json()["id"]

            response = await client.delete(f"/api/v1/chats/{session_id}", headers=headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_delete_session_not_found(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            response = await client.delete(
                "/api/v1/chats/00000000-0000-0000-0000-000000000000",
                headers=headers,
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_session_other_user_not_found(self):
        other_signup = {**_SIGNUP, "email": "chat_del_other@example.com", "phone_number": "01077778888"}
        other_login = {"email": "chat_del_other@example.com", "password": "Password123!"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers_a = await _get_auth_headers(client)
            create_resp = await client.post("/api/v1/chats", headers=headers_a, json={})
            session_id = create_resp.json()["id"]

            await client.post("/api/v1/auth/signup", json=other_signup)
            login_resp = await client.post("/api/v1/auth/login", json=other_login)
            headers_b = {"Authorization": f"Bearer {login_resp.json()['data']['access_token']}"}
            response = await client.delete(f"/api/v1/chats/{session_id}", headers=headers_b)

        assert response.status_code == status.HTTP_404_NOT_FOUND
