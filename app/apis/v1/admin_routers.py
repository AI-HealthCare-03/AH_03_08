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


# â”€â”€ 1. í”¼ë“œë°± ëª©ë¡ ì¡°íšŒ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@admin_router.get("/feedbacks", summary="í”¼ë“œë°± ëª©ë¡ ì¡°íšŒ (ê´€ë¦¬ìž)")
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
    return _ok({"total": total, "page": page, "limit": limit, "items": items}, "í”¼ë“œë°± ëª©ë¡ ì¡°íšŒ ì„±ê³µ")


# â”€â”€ 2. í”„ë¡¬í”„íŠ¸ ë²„ì „ í˜„í™© ì¡°íšŒ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@admin_router.get("/prompts/versions", summary="í”„ë¡¬í”„íŠ¸ ë²„ì „ë³„ ê°€ì´ë“œ í†µê³„")
async def get_prompt_versions(_: AdminUser):
    """
    Guide í…Œì´ë¸”ì˜ prompt_version ì»¬ëŸ¼ ê¸°ì¤€ìœ¼ë¡œ
    ë²„ì „ë³„ ê°€ì´ë“œ ìˆ˜ / í‰ê·  rating ì§‘ê³„
    """
    guides = await Guide.all().prefetch_related("feedbacks")
    version_map: dict[str, dict] = {}

    for g in guides:
        v = g.prompt_version or "unknown"
        if v not in version_map:
            version_map[v] = {"version": v, "guide_count": 0, "ratings": []}
        version_map[v]["guide_count"] += 1

    # í”¼ë“œë°± rating ì§‘ê³„
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
    return _ok(result, "í”„ë¡¬í”„íŠ¸ ë²„ì „ í†µê³„ ì¡°íšŒ ì„±ê³µ")


# â”€â”€ 3. AI í’ˆì§ˆ ëª¨ë‹ˆí„°ë§ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@admin_router.get("/metrics/summary", summary="AI í’ˆì§ˆ ëª¨ë‹ˆí„°ë§ ìš”ì•½")
async def get_metrics_summary(_: AdminUser):
    """
    - OCR ì„±ê³µ/ì‹¤íŒ¨ìœ¨
    - LLM ê°€ì´ë“œ ì„±ê³µ/ì‹¤íŒ¨ìœ¨
    - P95 latency (ModelMetric ê¸°ë°˜)
    - ì¼ë³„ ê°€ì´ë“œ ìƒì„± ìˆ˜ (ìµœê·¼ 7ì¼)
    """
    from datetime import datetime, timedelta

    # OCR ì„±ê³µ/ì‹¤íŒ¨ìœ¨
    total_records = await MedicalRecord.all().count()
    failed_records = await MedicalRecord.filter(status="FAILED").count()
    ocr_success_rate = round((1 - failed_records / total_records) * 100, 1) if total_records else 0

    # LLM ê°€ì´ë“œ ì„±ê³µ/ì‹¤íŒ¨ìœ¨
    total_guides = await Guide.all().count()
    failed_guides = await Guide.filter(status="failed").count()
    guide_success_rate = round((1 - failed_guides / total_guides) * 100, 1) if total_guides else 0

    # P95 latency (ModelMetric)
    metrics = await ModelMetric.filter(success=True).order_by("latency_ms").values_list("latency_ms", flat=True)
    p95_latency = None
    if metrics:
        idx = int(len(metrics) * 0.95)
        p95_latency = round(metrics[min(idx, len(metrics) - 1)], 1)

    # ìµœê·¼ 7ì¼ ì¼ë³„ ê°€ì´ë“œ ìƒì„± ìˆ˜
    now = datetime.now(UTC)
    daily_counts = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = await Guide.filter(created_at__gte=day_start, created_at__lt=day_end).count()
        daily_counts.append(
            {
                "date": day_start.strftime("%Y-%m-%d"),
                "guide_count": count,
            }
        )

    return _ok(
        {
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
        },
        "AI í’ˆì§ˆ ëª¨ë‹ˆí„°ë§ ì¡°íšŒ ì„±ê³µ",
    )


# â”€â”€ 4. ì‚¬ìš©ìž ëª©ë¡ ì¡°íšŒ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@admin_router.get("/users", summary="ì‚¬ìš©ìž ëª©ë¡ ì¡°íšŒ (ê´€ë¦¬ìž)")
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
    return _ok({"total": total, "page": page, "limit": limit, "items": items}, "ì‚¬ìš©ìž ëª©ë¡ ì¡°íšŒ ì„±ê³µ")


# 5. ÇÁ·ÒÇÁÆ® ¹öÀüº° ¼º´É ºñ±³ (2°³ ÀÌ»ó ÁöÇ¥)
@admin_router.get("/metrics/model-comparison", summary="ÇÁ·ÒÇÁÆ® ¹öÀüº° ¼º´É ºñ±³")
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
        result.append({
            "version": d["version"],
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
            "success_rate": round(sum(rates) / len(rates), 4) if rates else None,
            "avg_rating": round(sum(ratings) / len(ratings), 4) if ratings else None,
            "total_count": d["total_count"],
        })
    result.sort(key=lambda x: x["version"], reverse=True)
    return _ok(result, "¸ðµ¨ ¹öÀü ºñ±³ Á¶È¸ ¼º°ø")


# 6. ¹Ýº¹ Å×½ºÆ® ÆíÂ÷ ºÐ¼®
@admin_router.get("/metrics/consistency", summary="µ¿ÀÏ ÀÔ·Â ¹Ýº¹ Å×½ºÆ® ÆíÂ÷ ºÐ¼®")
async def get_consistency_analysis(_: AdminUser):
    from app.models.model_metrics import ModelMetric
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
        result.append({
            "model_type": model_type,
            "latency_stddev": round(statistics.stdev(lat), 2) if len(lat) >= 2 else None,
            "latency_mean": round(sum(lat) / len(lat), 2) if lat else None,
            "confidence_stddev": round(statistics.stdev(conf), 2) if len(conf) >= 2 else None,
            "confidence_mean": round(sum(conf) / len(conf), 4) if conf else None,
            "sample_count": len(lat),
        })
    return _ok(result, "¹Ýº¹ Å×½ºÆ® ÆíÂ÷ ºÐ¼® ¼º°ø")


# 7. ÇÇµå¹é ¼öÁý¡æÀúÀå¡æ°³¼± Èå¸§ ¿ä¾à
@admin_router.get("/metrics/feedback-flow", summary="ÇÇµå¹é ¼öÁý¡æ°³¼± Èå¸§ ¿ä¾à")
async def get_feedback_flow(_: AdminUser):
    from app.models.model_metrics import MetricSnapshot
    total_feedback = await Feedback.all().count()
    positive = await Feedback.filter(rating__gte=4).count()
    negative = await Feedback.filter(rating__lte=2).count()
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
    return _ok({
        "feedback_total": total_feedback,
        "positive_count": positive,
        "negative_count": negative,
        "improvement_trend": trend,
    }, "ÇÇµå¹é Èå¸§ ¿ä¾à ¼º°ø")


# 8. Å×½ºÆ® º¸°í¼­ ÀÚµ¿»ý¼º
@admin_router.get("/report", summary="3-3 ¹Ýº¹ Å×½ºÆ® º¸°í¼­ ÀÚµ¿»ý¼º")
async def generate_test_report(_: AdminUser):
    from datetime import datetime
    from app.models.model_metrics import MetricSnapshot, ModelMetric
    import statistics

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
    metrics = await ModelMetric.filter(success=True).values("model_type", "latency_ms", "confidence_score")
    snapshots = await MetricSnapshot.all().order_by("-snapshot_date").limit(30)
    feedbacks = await Feedback.all().count()
    positive = await Feedback.filter(rating__gte=4).count()

    type_map: dict[str, list] = {}
    for m in metrics:
        t = m["model_type"]
        if t not in type_map:
            type_map[t] = []
        if m["latency_ms"]:
            type_map[t].append(m["latency_ms"])

    consistency = []
    for model_type, latencies in type_map.items():
        consistency.append({
            "model_type": model_type,
            "mean_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
            "stddev_ms": round(statistics.stdev(latencies), 2) if len(latencies) >= 2 else None,
            "sample_count": len(latencies),
        })

    version_ratings = {}
    for s in snapshots:
        v = s.model_type
        if v not in version_ratings:
            version_ratings[v] = []
        if s.avg_rating:
            version_ratings[v].append(s.avg_rating)

    model_comparison = [
        {
            "version": v,
            "avg_rating": round(sum(r) / len(r), 4) if r else None,
        }
        for v, r in version_ratings.items()
    ]

    report = {
        "title": "MediLog 8Á¶ ? 3-3 ¹Ýº¹ Å×½ºÆ® º¸°í¼­",
        "generated_at": now,
        "summary": {
            "total_feedback": feedbacks,
            "positive_feedback": positive,
            "positive_rate_pct": round(positive / feedbacks * 100, 1) if feedbacks else 0,
        },
        "model_comparison": model_comparison,
        "consistency_analysis": consistency,
        "async_processing": {
            "description": "Celery ±â¹Ý ºñµ¿±â Ã³¸® Àû¿ë (OCR/LLM/Image Å¥ ºÐ¸®)",
            "queues": ["image", "llm"],
            "workers": ["ai-worker", "llm-worker"],
            "beat_tasks": ["daily-tip", "check-notifications", "daily-metric-snapshot"],
        },
        "feedback_structure": {
            "flow": "»ç¿ëÀÚ ÇÇµå¹é Á¦Ãâ ¡æ Feedback DB ÀúÀå ¡æ MetricSnapshot ½Ç½Ã°£ ¾÷µ¥ÀÌÆ® ¡æ ÀÏº° Áý°è ¡æ ÇÁ·ÒÇÁÆ® ¹öÀü °³¼±",
            "implemented": True,
        },
    }
    return _ok(report, "Å×½ºÆ® º¸°í¼­ »ý¼º ¼º°ø")