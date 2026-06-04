"""
internal_routers.py — Worker → FastAPI 콜백 수신 엔드포인트

[아키텍처 개선 12·13]
기존: Worker가 Tortoise ORM으로 DB를 직접 수정
      → app/models 와 ai_worker/models 이중 정의, 스키마 불일치 위험

개선:
  - Worker는 AI 처리(OCR·LLM·이미지·TTS)만 담당
  - 완료 후 POST /api/v1/internal/callback/{type} 으로 결과 전달
  - FastAPI가 DB 저장 + Redis Pub/Sub 발행 (SSE 클라이언트 알림)

보안:
  - X-Internal-Secret 헤더로 내부 서비스 인증
  - 외부에서 접근 불가 (Nginx에서 /api/v1/internal/ 경로 차단 권장)
"""

import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.config import config
from app.models.guide import Guide
from app.models.llm import GuideAsset
from app.models.medical_records import MedicalRecord

internal_router = APIRouter(prefix="/internal", tags=["internal"])


# ─────────────────────────────────────────────────────────────────
# 내부 인증 의존성
# ─────────────────────────────────────────────────────────────────


def verify_internal_secret(x_internal_secret: str = Header(...)) -> None:
    """Worker → FastAPI 내부 호출 인증. INTERNAL_SECRET 불일치 시 403."""
    if x_internal_secret != config.INTERNAL_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Internal secret mismatch.",
        )


InternalAuth = Depends(verify_internal_secret)


# ─────────────────────────────────────────────────────────────────
# 요청 스키마
# ─────────────────────────────────────────────────────────────────


class GuideCallbackRequest(BaseModel):
    guide_id: str
    user_id: int
    status: str  # "done" | "failed"
    medication_guide: str | None = None
    lifestyle_guide: str | None = None
    summary_text: str | None = None
    allergy_warnings: list = []
    condition_interactions: list = []
    # 신규 필드 (선택적 — 구버전 worker 호환)
    drug_interactions: list = []
    side_effects_watch: list = []
    medication_schedule: list = []
    urgent_warnings: list = []


class OcrCallbackRequest(BaseModel):
    record_id: str
    status: str  # "COMPLETED" | "FAILED"
    ocr_raw_text: str | None = None
    parsed_data: dict | None = None


class ImageCallbackRequest(BaseModel):
    record_id: str
    status: str  # "COMPLETED" | "FAILED"
    parsed_data: dict | None = None  # drug_info + confidence_score


class AssetCallbackRequest(BaseModel):
    asset_id: str
    guide_id: str
    status: str  # "DONE" | "FAILED"
    file_url: str | None = None  # TTS mp3 S3 URL


# ─────────────────────────────────────────────────────────────────
# [12] 콜백 엔드포인트 — Worker 완료 수신 → DB 저장 → Redis 발행
# ─────────────────────────────────────────────────────────────────


@internal_router.post("/callback/guide", dependencies=[InternalAuth])
async def guide_callback(body: GuideCallbackRequest, request: Request):
    """LLM Worker가 가이드 생성 완료/실패 후 호출."""
    if body.status == "done":

        def _to_json(val):
            if val is None:
                return None
            if isinstance(val, (dict, list)):
                return val
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                return {"raw": val}

        await Guide.filter(id=body.guide_id).update(
            status="done",
            medication_guide=_to_json(body.medication_guide),
            lifestyle_guide=_to_json(body.lifestyle_guide),
            summary_text=body.summary_text,
            allergy_warnings=body.allergy_warnings,
            condition_interactions=body.condition_interactions,
            drug_interactions=body.drug_interactions,
            side_effects_watch=body.side_effects_watch,
            medication_schedule=body.medication_schedule,
            urgent_warnings=body.urgent_warnings,
            llm_model="gpt-4o-mini",
        )
    else:
        await Guide.filter(id=body.guide_id).update(status="failed")

    redis = request.app.state.redis
    await redis.publish(
        f"guide:done:{body.user_id}",
        json.dumps({"guide_id": body.guide_id, "status": body.status}),
    )
    return {"ok": True}


@internal_router.post("/callback/ocr", dependencies=[InternalAuth])
async def ocr_callback(body: OcrCallbackRequest):
    """OCR Worker가 처방전 처리 완료/실패 시 호출."""
    if body.status == "COMPLETED":
        await MedicalRecord.filter(id=body.record_id).update(
            ocr_raw_text=body.ocr_raw_text,
            parsed_data=body.parsed_data,
            status="COMPLETED",
        )
    else:
        await MedicalRecord.filter(id=body.record_id).update(status="FAILED")
    return {"ok": True}


@internal_router.post("/callback/image", dependencies=[InternalAuth])
async def image_callback(body: ImageCallbackRequest):
    """Image Worker가 낱알약 분류 완료/실패 시 호출."""
    if body.status == "COMPLETED":
        await MedicalRecord.filter(id=body.record_id).update(
            parsed_data=body.parsed_data,
            status="COMPLETED",
        )
    else:
        await MedicalRecord.filter(id=body.record_id).update(status="FAILED")
    return {"ok": True}


@internal_router.post("/callback/asset", dependencies=[InternalAuth])
async def asset_callback(body: AssetCallbackRequest):
    """TTS/Image Worker가 에셋 생성 완료/실패 시 호출."""
    if body.status == "DONE" and body.file_url:
        await GuideAsset.filter(id=body.asset_id).update(
            file_url=body.file_url,
        )
    return {"ok": True}


# ─────────────────────────────────────────────────────────────────
# [13] SSE 엔드포인트 — 클라이언트가 가이드 완료를 실시간 수신
# ─────────────────────────────────────────────────────────────────


@internal_router.get("/guides/{guide_id}/stream")
async def guide_stream(guide_id: str, request: Request):
    """
    Server-Sent Events — 가이드 생성 완료를 클라이언트에 Push.

    클라이언트 사용 예:
        const es = new EventSource('/api/v1/internal/guides/{guide_id}/stream');
        es.onmessage = (e) => console.log(JSON.parse(e.data));

    Worker가 /callback/guide 를 호출하면 Redis Pub/Sub을 통해
    해당 user의 구독자에게 이벤트가 전달됩니다.
    """
    # guide 소유자 확인 (guide_id → user_id 조회)
    guide = await Guide.get_or_none(id=guide_id)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="가이드를 찾을 수 없습니다.")

    user_id = guide.user_id
    redis = request.app.state.redis

    async def event_generator():
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"guide:done:{user_id}")
        try:
            async for raw in pubsub.listen():
                if raw["type"] != "message":
                    continue
                data = json.loads(raw["data"])
                if data.get("guide_id") == guide_id:
                    yield f"data: {json.dumps(data)}\n\n"
                    break
                # 클라이언트 연결 끊김 감지
                if await request.is_disconnected():
                    break
        finally:
            await pubsub.unsubscribe(f"guide:done:{user_id}")
            await pubsub.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx SSE 버퍼링 비활성화
        },
    )
