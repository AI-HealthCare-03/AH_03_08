from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import ORJSONResponse

from app.dependencies.security import require_admin
from app.models.feedbacks import Feedback
from app.models.guide import Guide
from app.models.medical_records import MedicalRecord
from app.models.model_metrics import ModelMetric
from app.models.users import User

admin_router = APIRouter(prefix="/admin", tags=["admin"])

AdminUser = Annotated[User, Depends(require_admin)]


def _ok(data, message: str = "ok") -> dict:
    return {"success": True, "data": data, "message": message}


# ── 1. 피드백 목록 조회 ──────────────────────────────────────────

@admin_router.get("/feedbacks", summary="피드백 목록 조회 (관리자)")
async def list_feedbacks(
    _: AdminUser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    qs = Feedback.all().order_by("-created_at")
    total = await qs.count()
    rows = await qs.offset((page - 1) * limit).limit(limit)
    items = [
        {
            "feedback_id": str(f.id),
            "user_id": f.user_id,
            "guide_id": str(f.guide_id),
            "rating": f.rating,
            "comment": f.comment,
            "tag_ids": f.tag_ids or [],
            "status": f.status,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in rows
    ]
    return _ok({"total": total, "page": page, "limit": limit, "items": items}, "피드백 목록 조회 성공")


# ── 2. 프롬프트 버전 현황 조회 ───────────────────────────────────

@admin_router.get("/prompts/versions", summary="프롬프트 버전별 가이드 통계")
async def get_prompt_versions(_: AdminUser):
    """
    Guide 테이블의 prompt_version 컬럼 기준으로
    버전별 가이드 수 / 평균 rating 집계
    """
    guides = await Guide.all().prefetch_related("feedbacks")
    version_map: dict[str, dict] = {}

    for g in guides:
        v = g.prompt_version or "unknown"
        if v not in version_map:
            version_map[v] = {"version": v, "guide_count": 0, "ratings": []}
        version_map[v]["guide_count"] += 1

    # 피드백 rating 집계
    feedbacks = await Feedback.all()
    guide_version = {str(g.id): g.prompt_version or "unknown" for g in guides}
    for f in feedbacks:
        v = guide_version.get(str(f.guide_id), "unknown")
        if v in version_map:
            version_map[v]["ratings"].append(f.rating)

    result = []
    for v, d in version_map.items():
        ratings = d.pop("ratings")
        d["avg_rating"] = round(sum(ratings) / len(ratings), 2) if ratings else None
        d["feedback_count"] = len(ratings)
        result.append(d)

    result.sort(key=lambda x: x["version"], reverse=True)
    return _ok(result, "프롬프트 버전 통계 조회 성공")


# ── 3. AI 품질 모니터링 ──────────────────────────────────────────

@admin_router.get("/metrics/summary", summary="AI 품질 모니터링 요약")
async def get_metrics_summary(_: AdminUser):
    """
    - OCR 성공/실패율
    - LLM 가이드 성공/실패율
    - P95 latency (ModelMetric 기반)
    - 일별 가이드 생성 수 (최근 7일)
    """
    from tortoise.functions import Count
    from datetime import datetime, timedelta, timezone

    # OCR 성공/실패율
    total_records = await MedicalRecord.all().count()
    failed_records = await MedicalRecord.filter(status="FAILED").count()
    ocr_success_rate = round((1 - failed_records / total_records) * 100, 1) if total_records else 0

    # LLM 가이드 성공/실패율
    total_guides = await Guide.all().count()
    failed_guides = await Guide.filter(status="failed").count()
    guide_success_rate = round((1 - failed_guides / total_guides) * 100, 1) if total_guides else 0

    # P95 latency (ModelMetric)
    metrics = await ModelMetric.filter(success=True).order_by("latency_ms").values_list("latency_ms", flat=True)
    p95_latency = None
    if metrics:
        idx = int(len(metrics) * 0.95)
        p95_latency = round(metrics[min(idx, len(metrics) - 1)], 1)

    # 최근 7일 일별 가이드 생성 수
    now = datetime.now(timezone.utc)
    daily_counts = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = await Guide.filter(created_at__gte=day_start, created_at__lt=day_end).count()
        daily_counts.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "guide_count": count,
        })

    return _ok({
        "ocr": {
            "total": total_records,
            "failed": failed_records,
            "success_rate_pct": ocr_success_rate,
        },
        "llm": {
            "total": total_guides,
            "failed": failed_guides,
            "success_rate_pct": guide_success_rate,
        },
        "p95_latency_ms": p95_latency,
        "daily_guides": daily_counts,
    }, "AI 품질 모니터링 조회 성공")


# ── 4. 사용자 목록 조회 ──────────────────────────────────────────

@admin_router.get("/users", summary="사용자 목록 조회 (관리자)")
async def list_users(
    _: AdminUser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    qs = User.all().order_by("-created_at")
    total = await qs.count()
    rows = await qs.offset((page - 1) * limit).limit(limit)
    items = [
        {
            "user_id": r.id,
            "email": r.email,
            "name": r.name,
            "is_admin": r.is_admin,
            "is_active": r.is_active,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return _ok({"total": total, "page": page, "limit": limit, "items": items}, "사용자 목록 조회 성공")