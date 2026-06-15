"""가이드 평가 스크립트 공통 (로그인·폴링)."""

import asyncio
import os
import uuid
from typing import Any

import httpx

BASE_URL = os.getenv("EVAL_API_BASE", "http://127.0.0.1:8000/api/v1")
POLL_INTERVAL_SEC = float(os.getenv("EVAL_POLL_INTERVAL", "3"))
POLL_MAX = int(os.getenv("EVAL_POLL_MAX", "40"))

COMPARE_FIELDS = (
    "medication_guide",
    "lifestyle_guide",
    "summary",
    "allergy_warnings",
    "condition_interactions",
)


async def login_client() -> tuple[httpx.AsyncClient, dict[str, str]]:
    email = os.getenv("EVAL_EMAIL")
    password = os.getenv("EVAL_PASSWORD", "Password123!")

    client = httpx.AsyncClient(base_url=BASE_URL, timeout=120.0)
    if email:
        r = await client.post("/auth/login", json={"email": email, "password": password})
        r.raise_for_status()
    else:
        email = f"eval_{uuid.uuid4().hex[:8]}@example.com"
        phone = f"010{uuid.uuid4().int % 10**8:08d}"
        await client.post(
            "/auth/signup",
            json={
                "email": email,
                "password": password,
                "name": "평가테스트",
                "gender": "FEMALE",
                "birth_date": "1995-05-20",
                "phone_number": phone,
            },
        )
        r = await client.post("/auth/login", json={"email": email, "password": password})
        r.raise_for_status()

    body = r.json()
    token = body.get("access_token") or (body.get("data") or {}).get("access_token")
    if not token:
        raise RuntimeError(f"login response missing access_token: {body}")
    return client, {"Authorization": f"Bearer {token}"}


async def setup_health_and_record(client: httpx.AsyncClient, headers: dict[str, str]) -> str:
    await client.post(
        "/health/allergies",
        headers=headers,
        json={"allergy_name": "페니실린", "severity": "severe"},
    )
    await client.post(
        "/health/diseases",
        headers=headers,
        json={"underlying_disease_name": "고혈압", "severity": "moderate"},
    )
    r = await client.post(
        "/health/records",
        headers=headers,
        json={
            "record_type": 0,
            "parsed_data": {
                "medications": [
                    {
                        "drug_name": "타이레놀",
                        "dosage": "500mg",
                        "frequency": "1일 3회",
                        "duration": "7일",
                    }
                ]
            },
        },
    )
    r.raise_for_status()
    return str(r.json()["id"])


async def poll_guide_done(client: httpx.AsyncClient, headers: dict[str, str], guide_id: str) -> tuple[str, int]:
    status = "processing"
    polls = 0
    for _ in range(POLL_MAX):
        r = await client.get(f"/guides/{guide_id}/status", headers=headers)
        r.raise_for_status()
        status = r.json()["data"]["status"]
        polls += 1
        if status in ("done", "failed"):
            return status, polls
        await asyncio.sleep(POLL_INTERVAL_SEC)
    return status, polls


async def fetch_guide(client: httpx.AsyncClient, headers: dict[str, str], guide_id: str) -> dict[str, Any]:
    r = await client.get(f"/guides/{guide_id}", headers=headers)
    r.raise_for_status()
    return r.json()["data"]


def pick_compare_fields(guide: dict[str, Any]) -> dict[str, Any]:
    return {k: guide.get(k) for k in COMPARE_FIELDS}
