from io import BytesIO
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

_SIGNUP = {
    "email": "record_test@example.com",
    "password": "Password123!",
    "name": "기록테스터",
    "gender": "FEMALE",
    "birth_date": "1995-03-15",
    "phone_number": "01055556666",
}
_LOGIN = {"email": "record_test@example.com", "password": "Password123!"}
_FAKE_IMAGE = ("test.jpg", BytesIO(b"\xff\xd8\xff" + b"fake image content"), "image/jpeg")


async def _get_auth_headers(client: AsyncClient) -> dict:
    await client.post("/api/v1/auth/signup", json=_SIGNUP)
    resp = await client.post("/api/v1/auth/login", json=_LOGIN)
    return {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}


class TestUploadRecordAPI(TestCase):
    async def test_upload_success(self):
        with patch("app.application.medical_record.use_cases.upload_record._celery") as mock_celery:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = await _get_auth_headers(client)
                response = await client.post(
                    "/api/v1/records/upload",
                    headers=headers,
                    data={"record_type": 0},
                    files={"file": _FAKE_IMAGE},
                )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "id" in data
        assert data["status"] == "PENDING"
        assert data["record_type"] == 0
        mock_celery.send_task.assert_called_once()

    async def test_upload_invalid_file_type(self):
        with patch("app.application.medical_record.use_cases.upload_record._celery"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = await _get_auth_headers(client)
                response = await client.post(
                    "/api/v1/records/upload",
                    headers=headers,
                    data={"record_type": 0},
                    files={"file": ("test.txt", BytesIO(b"text content"), "text/plain")},
                )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_upload_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/records/upload",
                data={"record_type": 0},
                files={"file": _FAKE_IMAGE},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetRecordAPI(TestCase):
    async def test_get_record_success(self):
        with patch("app.application.medical_record.use_cases.upload_record._celery"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = await _get_auth_headers(client)

                upload_resp = await client.post(
                    "/api/v1/records/upload",
                    headers=headers,
                    data={"record_type": 0},
                    files={"file": _FAKE_IMAGE},
                )
                record_id = upload_resp.json()["id"]

                response = await client.get(f"/api/v1/records/{record_id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == record_id

    async def test_get_record_not_found(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await _get_auth_headers(client)
            response = await client.get(
                "/api/v1/records/00000000-0000-0000-0000-000000000000",
                headers=headers,
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_record_other_user_forbidden(self):
        other_signup = {**_SIGNUP, "email": "other_record@example.com", "phone_number": "01077778888"}
        other_login = {"email": "other_record@example.com", "password": "Password123!"}

        with patch("app.application.medical_record.use_cases.upload_record._celery"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # 첫 번째 유저가 업로드
                headers_a = await _get_auth_headers(client)
                upload_resp = await client.post(
                    "/api/v1/records/upload",
                    headers=headers_a,
                    data={"record_type": 0},
                    files={"file": _FAKE_IMAGE},
                )
                record_id = upload_resp.json()["id"]

                # 두 번째 유저가 조회 시도
                await client.post("/api/v1/auth/signup", json=other_signup)
                login_resp = await client.post("/api/v1/auth/login", json=other_login)
                headers_b = {"Authorization": f"Bearer {login_resp.json()['data']['access_token']}"}
                response = await client.get(f"/api/v1/records/{record_id}", headers=headers_b)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestListRecordsAPI(TestCase):
    async def test_list_records_success(self):
        with patch("app.application.medical_record.use_cases.upload_record._celery"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = await _get_auth_headers(client)

                for _ in range(3):
                    await client.post(
                        "/api/v1/records/upload",
                        headers=headers,
                        data={"record_type": 0},
                        files={"file": _FAKE_IMAGE},
                    )

                response = await client.get("/api/v1/records", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["page"] == 1

    async def test_list_records_pagination(self):
        with patch("app.application.medical_record.use_cases.upload_record._celery"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = await _get_auth_headers(client)

                for _ in range(5):
                    await client.post(
                        "/api/v1/records/upload",
                        headers=headers,
                        data={"record_type": 0},
                        files={"file": _FAKE_IMAGE},
                    )

                response = await client.get("/api/v1/records?page=1&limit=2", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2


class TestUpdateRecordAPI(TestCase):
    async def test_update_record_success(self):
        parsed_data = {"medications": [{"name": "타이레놀", "dosage": "500mg"}]}

        with patch("app.application.medical_record.use_cases.upload_record._celery"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = await _get_auth_headers(client)

                upload_resp = await client.post(
                    "/api/v1/records/upload",
                    headers=headers,
                    data={"record_type": 0},
                    files={"file": _FAKE_IMAGE},
                )
                record_id = upload_resp.json()["id"]

                response = await client.put(
                    f"/api/v1/records/{record_id}",
                    headers=headers,
                    json={"parsed_data": parsed_data},
                )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["parsed_data"] == parsed_data

    async def test_update_record_other_user_forbidden(self):
        other_signup = {**_SIGNUP, "email": "other_update@example.com", "phone_number": "01011119999"}
        other_login = {"email": "other_update@example.com", "password": "Password123!"}

        with patch("app.application.medical_record.use_cases.upload_record._celery"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers_a = await _get_auth_headers(client)
                upload_resp = await client.post(
                    "/api/v1/records/upload",
                    headers=headers_a,
                    data={"record_type": 0},
                    files={"file": _FAKE_IMAGE},
                )
                record_id = upload_resp.json()["id"]

                await client.post("/api/v1/auth/signup", json=other_signup)
                login_resp = await client.post("/api/v1/auth/login", json=other_login)
                headers_b = {"Authorization": f"Bearer {login_resp.json()['data']['access_token']}"}
                response = await client.put(
                    f"/api/v1/records/{record_id}",
                    headers=headers_b,
                    json={"parsed_data": {"medications": []}},
                )

        assert response.status_code == status.HTTP_403_FORBIDDEN
