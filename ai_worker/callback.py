"""
ai_worker/callback.py — FastAPI 내부 콜백 호출 헬퍼

Worker 태스크가 완료/실패 후 이 모듈을 통해 FastAPI에 결과를 전달한다.
FastAPI가 DB 저장과 Redis Pub/Sub 발행을 담당하므로
Worker는 ai_worker/models.py의 이중 정의 ORM 모델을 사용하지 않아도 된다.
"""

import logging

import httpx

from ai_worker.core.config import config

logger = logging.getLogger(__name__)

_HEADERS = {
    "Content-Type": "application/json",
    "X-Internal-Secret": config.INTERNAL_SECRET,
}
_TIMEOUT = 10.0  # 초


def _post(path: str, payload: dict) -> bool:
    """동기 HTTP POST — Celery 태스크는 동기 컨텍스트에서 실행됨."""
    url = f"{config.APP_INTERNAL_URL}/api/v1/internal{path}"
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(url, json=payload, headers=_HEADERS)
            resp.raise_for_status()
            return True
    except httpx.HTTPError as exc:
        logger.error(f"[callback] POST {path} 실패: {exc}")
        return False


# ── 콜백 함수 ────────────────────────────────────────────────────


def guide_done(
    guide_id: str,
    user_id: int,
    medication_guide: str,
    lifestyle_guide: str,
    summary_text: str,
    allergy_warnings: list,
    condition_interactions: list,
    # 신규 필드 (선택적 — 구버전 호환 유지)
    drug_interactions: list | None = None,
    side_effects_watch: list | None = None,
    medication_schedule: list | None = None,
    urgent_warnings: list | None = None,
) -> bool:
    payload: dict = {
        "guide_id": guide_id,
        "user_id": user_id,
        "status": "done",
        "medication_guide": medication_guide,
        "lifestyle_guide": lifestyle_guide,
        "summary_text": summary_text,
        "allergy_warnings": allergy_warnings,
        "condition_interactions": condition_interactions,
    }
    # None이 아닌 필드만 포함 (DB 컬럼이 없는 경우 FastAPI가 무시)
    if drug_interactions is not None:
        payload["drug_interactions"] = drug_interactions
    if side_effects_watch is not None:
        payload["side_effects_watch"] = side_effects_watch
    if medication_schedule is not None:
        payload["medication_schedule"] = medication_schedule
    if urgent_warnings is not None:
        payload["urgent_warnings"] = urgent_warnings
    return _post("/callback/guide", payload)


def guide_failed(guide_id: str, user_id: int) -> bool:
    return _post(
        "/callback/guide",
        {
            "guide_id": guide_id,
            "user_id": user_id,
            "status": "failed",
        },
    )


def ocr_done(record_id: str, ocr_raw_text: str, parsed_data: dict) -> bool:
    return _post(
        "/callback/ocr",
        {
            "record_id": record_id,
            "status": "COMPLETED",
            "ocr_raw_text": ocr_raw_text,
            "parsed_data": parsed_data,
        },
    )


def ocr_failed(record_id: str) -> bool:
    return _post(
        "/callback/ocr",
        {
            "record_id": record_id,
            "status": "FAILED",
        },
    )


def image_done(record_id: str, parsed_data: dict) -> bool:
    return _post(
        "/callback/image",
        {
            "record_id": record_id,
            "status": "COMPLETED",
            "parsed_data": parsed_data,
        },
    )


def image_failed(record_id: str) -> bool:
    return _post(
        "/callback/image",
        {
            "record_id": record_id,
            "status": "FAILED",
        },
    )


def asset_done(asset_id: str, guide_id: str, file_url: str) -> bool:
    return _post(
        "/callback/asset",
        {
            "asset_id": asset_id,
            "guide_id": guide_id,
            "status": "DONE",
            "file_url": file_url,
        },
    )


def asset_failed(asset_id: str, guide_id: str) -> bool:
    return _post(
        "/callback/asset",
        {
            "asset_id": asset_id,
            "guide_id": guide_id,
            "status": "FAILED",
        },
    )