"""Swagger 동일 플로우: 건강정보 등록 → 가이드 생성 → 상태/상세 확인."""

import asyncio
import time
import uuid

import httpx

BASE = "http://127.0.0.1:8000/api/v1"
EMAIL = f"health_verify_{uuid.uuid4().hex[:8]}@example.com"
PASSWORD = "Password123!"


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE, timeout=60.0) as client:
        # 1. 회원가입 / 로그인
        r = await client.post(
            "/auth/signup",
            json={
                "email": EMAIL,
                "password": PASSWORD,
                "name": "건강검증",
                "gender": "FEMALE",
                "birth_date": "1995-05-20",
                "phone_number": "01099998888",
            },
        )
        print("signup", r.status_code)
        r.raise_for_status()

        r = await client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
        r.raise_for_status()
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. 알러지 / 기저질환
        r = await client.post(
            "/health/allergies",
            headers=headers,
            json={"allergy_name": "페니실린", "severity": "severe"},
        )
        print("allergy", r.status_code, r.text[:200])
        r.raise_for_status()

        r = await client.post(
            "/health/diseases",
            headers=headers,
            json={"underlying_disease_name": "고혈압", "severity": "moderate"},
        )
        print("disease", r.status_code, r.text[:200])
        r.raise_for_status()

        r = await client.get("/health/allergies", headers=headers)
        print("allergies list", r.status_code, r.json())
        r = await client.get("/health/diseases", headers=headers)
        print("diseases list", r.status_code, r.json())

        # 3. 진료기록 (약품 OCR 데이터)
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
        print("record", r.status_code, r.text[:300])
        r.raise_for_status()
        record_id = str(r.json()["id"])

        # 4. 가이드 생성
        r = await client.post("/guides/generate", headers=headers, json={"record_id": record_id})
        print("generate", r.status_code, r.json())
        r.raise_for_status()
        guide_id = r.json()["data"]["guide_id"]

        # 5. 상태 폴링
        status = "processing"
        for i in range(40):
            r = await client.get(f"/guides/{guide_id}/status", headers=headers)
            r.raise_for_status()
            status = r.json()["data"]["status"]
            print(f"poll {i}: {status}")
            if status in ("done", "failed"):
                break
            await asyncio.sleep(3)

        # 6. 상세
        r = await client.get(f"/guides/{guide_id}", headers=headers)
        r.raise_for_status()
        data = r.json()["data"]
        print("guide status:", status)
        print("medication_guide len:", len(data.get("medication_guide") or ""))
        print("allergy_warnings:", data.get("allergy_warnings"))
        print("condition_interactions:", data.get("condition_interactions"))

        if status != "done":
            raise SystemExit(f"guide ended with status={status}")
        print("OK: Swagger flow verified")


if __name__ == "__main__":
    asyncio.run(main())
