# app/apis/v1/notification_routers.py
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies.security import get_request_user
from app.models.notifications import Notification

notification_router = APIRouter(prefix="/notifications", tags=["notifications"])


def _ok(data):
    return {"success": True, "data": data, "message": "ok"}


class NotificationCreateRequest(BaseModel):
    medication_id: str = Field(..., description="medication UUID")
    title: str = Field(..., max_length=200)
    type: Literal["push", "email"] = "push"
    scheduled_time: str = Field(..., description="HH:MM:SS")


class NotificationUpdateRequest(BaseModel):
    is_active: bool | None = None
    scheduled_time: str | None = None


class NotificationResponse(BaseModel):
    id: str
    medication_id: str
    title: str
    type: str
    scheduled_time: str
    is_active: bool
    end_date: str | None = None
    created_at: str


@notification_router.get("", summary="List notifications")
async def list_notifications(current_user=Depends(get_request_user)):
    rows = await Notification.filter(user_id=current_user.id).order_by("scheduled_time").prefetch_related("medication")
    today = date.today()
    expired_ids = []
    result = []
    for r in rows:
        end_date = getattr(r.medication, "end_date", None)
        if r.is_active and end_date and end_date < today:
            r.is_active = False
            expired_ids.append(r.id)
        result.append(NotificationResponse(
            id=str(r.id),
            medication_id=str(r.medication_id),
            title=r.title,
            type=r.type,
            scheduled_time=str(r.scheduled_time),
            is_active=r.is_active,
            end_date=str(end_date) if end_date else None,
            created_at=str(r.created_at),
        ))
    if expired_ids:
        await Notification.filter(id__in=expired_ids).update(is_active=False)
    return _ok(result)


@notification_router.post("", summary="Create notification", status_code=status.HTTP_201_CREATED)
async def create_notification(body: NotificationCreateRequest, current_user=Depends(get_request_user)):
    from app.models.medical_records import MedicalRecord
    from app.models.medications import Medication

    med = await Medication.filter(id=body.medication_id).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found.")
    record = await MedicalRecord.filter(id=med.medical_record_id, user_id=current_user.id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found.")
    row = await Notification.create(
        user_id=current_user.id,
        medication_id=body.medication_id,
        title=body.title,
        type=body.type,
        scheduled_time=body.scheduled_time,
        is_active=True,
    )

    # 오늘부터 30일치 캘린더 이벤트 자동 생성 (중복 제외)
    from app.models.calendar_events import CalendarEvent

    today = date.today()
    existing_dates = set(
        str(e.event_date)
        for e in await CalendarEvent.filter(
            user_id=current_user.id,
            medication_id=body.medication_id,
            scheduled_time=body.scheduled_time,
            event_date__gte=today,
            event_date__lt=today + timedelta(days=30),
        ).only("event_date")
    )
    new_events = [
        CalendarEvent(
            user_id=current_user.id,
            medication_id=body.medication_id,
            event_date=today + timedelta(days=i),
            scheduled_time=body.scheduled_time,
            status="PENDING",
        )
        for i in range(30)
        if str(today + timedelta(days=i)) not in existing_dates
    ]
    if new_events:
        await CalendarEvent.bulk_create(new_events)

    return _ok(
        NotificationResponse(
            id=str(row.id),
            medication_id=str(row.medication_id),
            title=row.title,
            type=row.type,
            scheduled_time=str(row.scheduled_time),
            is_active=row.is_active,
            created_at=str(row.created_at),
        )
    )


@notification_router.put("/{notification_id}", summary="Toggle notification")
async def update_notification(
    notification_id: str, body: NotificationUpdateRequest, current_user=Depends(get_request_user)
):
    row = await Notification.filter(id=notification_id, user_id=current_user.id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    update_fields = []
    if body.is_active is not None:
        row.is_active = body.is_active
        update_fields.append("is_active")
    if body.scheduled_time is not None:
        row.scheduled_time = body.scheduled_time
        update_fields.append("scheduled_time")
    if update_fields:
        await row.save(update_fields=update_fields)
    return _ok(
        NotificationResponse(
            id=str(row.id),
            medication_id=str(row.medication_id),
            title=row.title,
            type=row.type,
            scheduled_time=str(row.scheduled_time),
            is_active=row.is_active,
            created_at=str(row.created_at),
        )
    )


@notification_router.delete("/{notification_id}", summary="Delete notification")
async def delete_notification(notification_id: str, current_user=Depends(get_request_user)):
    row = await Notification.filter(id=notification_id, user_id=current_user.id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    from app.models.calendar_events import CalendarEvent

    today = date.today()
    await CalendarEvent.filter(
        user_id=current_user.id,
        medication_id=row.medication_id,
        scheduled_time=row.scheduled_time,
        event_date__gte=today,
        status="PENDING",
    ).delete()
    await row.delete()
    return _ok({"message": "Deleted."})
