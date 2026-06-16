from datetime import UTC
from typing import Annotated

from fastapi import APIRouter, Depends, Query

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


@admin_router.get("/feedbacks", summary="feedback list")
async def list_feedbacks(
    _: AdminUser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    qs = Feedback.all().order_by("-created_at")
    total = await qs.count()
    rows = await qs.offset((page - 1) * limit).limit(limit).prefetch_related("user")
    items = [
        {
            "feedback_id": str(f.id),
            "user_id": f.user_id,
            "user_email": f.user.email if f.user else None,
            "guide_id": str(f.guide_id),
            "rating": f.rating,
            "comment": f.comment,
            "tag_ids": f.tag_ids or [],
            "status": f.status,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in rows
    ]
    return _ok({"total": total, "page": page, "limit": limit, "items": items}, "ok")


@admin_router.get("/prompts/current", summary="current prompt text")
async def get_current_prompts(_: AdminUser):
    from ai_worker.prompts.llm_prompts import CHAT_BASE_SYSTEM, GUIDE_SYSTEM

    return _ok({"guide_system": GUIDE_SYSTEM, "chat_system": CHAT_BASE_SYSTEM}, "ok")


@admin_router.get("/prompts/versions", summary="prompt version stats")
async def get_prompt_versions(_: AdminUser):
    guides = await Guide.all().prefetch_related("feedbacks")
    version_map: dict[str, dict] = {}
    for g in guides:
        v = g.prompt_version or "unknown"
        if v not in version_map:
            version_map[v] = {"version": v, "guide_count": 0, "ratings": []}
        version_map[v]["guide_count"] += 1
    feedbacks = await Feedback.all()
    guide_version = {str(g.id): g.prompt_version or "unknown" for g in guides}
    for f in feedbacks:
        v = guide_version.get(str(f.guide_id), "unknown")
        if v in version_map:
            version_map[v]["ratings"].append(f.rating)
    result = []
    for d in version_map.values():
        ratings = d.pop("ratings")
        d["avg_rating"] = round(sum(ratings) / len(ratings), 2) if ratings else None
        d["feedback_count"] = len(ratings)
        result.append(d)
    result.sort(key=lambda x: x["version"], reverse=True)
    return _ok(result, "ok")


@admin_router.get("/metrics/summary", summary="AI metrics summary")
async def get_metrics_summary(_: AdminUser):
    from datetime import datetime, timedelta

    total_records = await MedicalRecord.all().count()
    failed_records = await MedicalRecord.filter(status="FAILED").count()
    ocr_success_rate = round((1 - failed_records / total_records) * 100, 1) if total_records else 0
    total_guides = await Guide.all().count()
    failed_guides = await Guide.filter(status="failed").count()
    guide_success_rate = round((1 - failed_guides / total_guides) * 100, 1) if total_guides else 0
    metrics = await ModelMetric.filter(success=True).order_by("latency_ms").values_list("latency_ms", flat=True)
    p95_latency = None
    if metrics:
        idx = int(len(metrics) * 0.95)
        p95_latency = round(metrics[min(idx, len(metrics) - 1)], 1)
    now = datetime.now(UTC)
    daily_counts = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = await Guide.filter(created_at__gte=day_start, created_at__lt=day_end).count()
        daily_counts.append({"date": day_start.strftime("%Y-%m-%d"), "guide_count": count})
    return _ok(
        {
            "ocr": {"total": total_records, "failed": failed_records, "success_rate_pct": ocr_success_rate},
            "llm": {"total": total_guides, "failed": failed_guides, "success_rate_pct": guide_success_rate},
            "p95_latency_ms": p95_latency,
            "daily_guides": daily_counts,
        },
        "ok",
    )


@admin_router.get("/users", summary="user list")
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
    return _ok({"total": total, "page": page, "limit": limit, "items": items}, "ok")


@admin_router.get("/metrics/model-comparison", summary="model version comparison")
async def get_model_comparison(_: AdminUser):
    from app.models.model_metrics import MetricSnapshot

    snapshots = await MetricSnapshot.all().order_by("model_type", "snapshot_date")
    version_map: dict[str, dict] = {}
    for s in snapshots:
        v = s.model_type
        if v not in version_map:
            version_map[v] = {
                "version": v,
                "avg_latency_ms": [],
                "success_rates": [],
                "avg_ratings": [],
                "total_count": 0,
            }
        if s.avg_latency_ms is not None:
            version_map[v]["avg_latency_ms"].append(s.avg_latency_ms)
        if s.success_rate is not None:
            version_map[v]["success_rates"].append(s.success_rate)
        if s.avg_rating is not None:
            version_map[v]["avg_ratings"].append(s.avg_rating)
        version_map[v]["total_count"] += s.total_count or 0
    result = []
    for d in version_map.values():
        latencies = d["avg_latency_ms"]
        rates = d["success_rates"]
        ratings = d["avg_ratings"]
        result.append(
            {
                "version": d["version"],
                "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
                "success_rate": round(sum(rates) / len(rates), 4) if rates else None,
                "avg_rating": round(sum(ratings) / len(ratings), 4) if ratings else None,
                "total_count": d["total_count"],
            }
        )
    result.sort(key=lambda x: x["version"], reverse=True)
    return _ok(result, "ok")


@admin_router.get("/metrics/consistency", summary="consistency analysis")
async def get_consistency_analysis(_: AdminUser):
    import statistics

    metrics = await ModelMetric.filter(success=True).values("model_type", "latency_ms", "confidence_score")
    type_map: dict[str, dict] = {}
    for m in metrics:
        t = m["model_type"]
        if t not in type_map:
            type_map[t] = {"latencies": [], "confidences": []}
        if m["latency_ms"] is not None:
            type_map[t]["latencies"].append(m["latency_ms"])
        if m["confidence_score"] is not None:
            type_map[t]["confidences"].append(m["confidence_score"])
    result = []
    for model_type, data in type_map.items():
        lat = data["latencies"]
        conf = data["confidences"]
        result.append(
            {
                "model_type": model_type,
                "latency_stddev": round(statistics.stdev(lat), 2) if len(lat) >= 2 else None,
                "latency_mean": round(sum(lat) / len(lat), 2) if lat else None,
                "confidence_stddev": round(statistics.stdev(conf), 2) if len(conf) >= 2 else None,
                "confidence_mean": round(sum(conf) / len(conf), 4) if conf else None,
                "sample_count": len(lat),
            }
        )
    return _ok(result, "ok")


@admin_router.get("/metrics/feedback-flow", summary="feedback flow summary")
async def get_feedback_flow(_: AdminUser):
    from app.models.model_metrics import MetricSnapshot

    total_feedback = await Feedback.all().count()
    positive = await Feedback.filter(rating=1).count()
    negative = await Feedback.filter(rating=0).count()
    snapshots = await MetricSnapshot.all().order_by("-snapshot_date").limit(14)
    trend = [
        {
            "date": str(s.snapshot_date),
            "model_type": s.model_type,
            "avg_rating": s.avg_rating,
            "success_rate": s.success_rate,
            "avg_latency_ms": s.avg_latency_ms,
        }
        for s in snapshots
    ]
    return _ok(
        {
            "feedback_total": total_feedback,
            "positive_count": positive,
            "negative_count": negative,
            "improvement_trend": trend,
        },
        "ok",
    )


@admin_router.get("/report", summary="test report")
async def generate_test_report(_: AdminUser):
    import statistics
    from datetime import datetime

    from app.models.model_metrics import MetricSnapshot

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
    metrics = await ModelMetric.filter(success=True).values("model_type", "latency_ms", "confidence_score")
    snapshots = await MetricSnapshot.all().order_by("-snapshot_date").limit(30)
    feedbacks = await Feedback.all().count()
    positive = await Feedback.filter(rating=1).count()
    type_map: dict[str, list] = {}
    for m in metrics:
        t = m["model_type"]
        if t not in type_map:
            type_map[t] = []
        if m["latency_ms"]:
            type_map[t].append(m["latency_ms"])
    consistency = [
        {
            "model_type": model_type,
            "mean_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
            "stddev_ms": round(statistics.stdev(latencies), 2) if len(latencies) >= 2 else None,
            "sample_count": len(latencies),
        }
        for model_type, latencies in type_map.items()
    ]
    version_ratings: dict[str, list] = {}
    for s in snapshots:
        v = s.model_type
        if v not in version_ratings:
            version_ratings[v] = []
        if s.avg_rating:
            version_ratings[v].append(s.avg_rating)
    model_comparison = [
        {"version": v, "avg_rating": round(sum(r) / len(r), 4) if r else None} for v, r in version_ratings.items()
    ]
    report = {
        "title": "MediLog 8\uc870 \u2014 3-3 \ubc18\ubcf5 \ud14c\uc2a4\ud2b8 \ubcf4\uace0\uc11c",
        "generated_at": now,
        "summary": {
            "total_feedback": feedbacks,
            "positive_feedback": positive,
            "positive_rate_pct": round(positive / feedbacks * 100, 1) if feedbacks else 0,
        },
        "model_comparison": model_comparison,
        "consistency_analysis": consistency,
        "async_processing": {
            "description": "Celery \uae30\ubc18 \ube44\ub3d9\uae30 \ucc98\ub9ac \uc801\uc6a9 (OCR/LLM/Image \ud050 \ubd84\ub9ac)",
            "queues": ["image", "llm"],
            "workers": ["ai-worker", "llm-worker"],
            "beat_tasks": ["daily-tip", "check-notifications", "daily-metric-snapshot"],
        },
        "feedback_structure": {
            "flow": "\uc0ac\uc6a9\uc790 \ud53c\ub4dc\ubc31 \uc81c\ucd9c \u2192 Feedback DB \uc800\uc7a5 \u2192 MetricSnapshot \uc2e4\uc2dc\uac04 \uc5c5\ub370\uc774\ud2b8 \u2192 \uc77c\ubcc4 \uc9d1\uacc4 \u2192 \ud504\ub86c\ud504\ud2b8 \ubc84\uc804 \uac1c\uc120",
            "implemented": True,
        },
    }
    return _ok(report, "ok")
