from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse

from app.dependencies.security import get_request_user
from app.models.guide import Guide
from app.models.medical_records import MedicalRecord
from app.models.notifications import Notification
from app.models.users import User

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])

CurrentUser = Annotated[User, Depends(get_request_user)]


@dashboard_router.get("", summary="홈 대시보드 통합 조회")
async def get_dashboard(current_user: CurrentUser):
    user_data = {
        "name": current_user.name,
        "height_cm": current_user.height_cm,
        "weight_kg": current_user.weight_kg,
    }

    record_count = await MedicalRecord.filter(user_id=current_user.id).count()

    active_notification_count = await Notification.filter(
        user_id=current_user.id, is_active=True
    ).count()

    recent_records_qs = await (
        MedicalRecord.filter(user_id=current_user.id)
        .order_by("-created_at")
        .limit(5)
    )
    recent_records = [
        {
            "record_id": str(r.id),
            "record_type": r.record_type,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in recent_records_qs
    ]

    latest_guide_qs = (
        await Guide.filter(user_id=current_user.id)
        .order_by("-created_at")
        .first()
    )
    latest_guide = None
    if latest_guide_qs:
        latest_guide = {
            "guide_id": str(latest_guide_qs.id),
            "status": latest_guide_qs.status,
            "summary_text": latest_guide_qs.summary_text,
            "created_at": latest_guide_qs.created_at.isoformat() if latest_guide_qs.created_at else None,
        }

    today_notifications = await Notification.filter(
        user_id=current_user.id, is_active=True
    ).prefetch_related("medication")

    today_medications = []
    for n in today_notifications:
        try:
            med = n.medication
            today_medications.append({
                "notification_id": str(n.id),
                "drug_name": med.drug_name,
                "scheduled_time": str(n.scheduled_time),
                "is_active": n.is_active,
            })
        except Exception:
            continue

    return ORJSONResponse({
        "success": True,
        "data": {
            "user": user_data,
            "summary": {
                "record_count": record_count,
                "active_notification_count": active_notification_count,
            },
            "recent_records": recent_records,
            "latest_guide": latest_guide,
            "today_medications": today_medications,
        },
        "message": "대시보드 조회 성공",
    })