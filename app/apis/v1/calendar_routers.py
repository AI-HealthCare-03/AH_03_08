# app/apis/v1/calendar_routers.py
from datetime import UTC, date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.dependencies.security import get_request_user
from app.models.calendar_events import CalendarEvent

calendar_router = APIRouter(prefix="/calendars", tags=["calendars"])


def _ok(data):
    return {"success": True, "data": data, "message": "ok"}


class CalendarEventCreateRequest(BaseModel):
    medication_id: str
    event_date: str = Field(..., description="YYYY-MM-DD")
    scheduled_time: str = Field(..., description="HH:MM:SS")
    note: str | None = None


class CalendarStatusUpdateRequest(BaseModel):
    status: Literal["PENDING", "TAKEN", "MISSED"]


class CalendarEventResponse(BaseModel):
    id: str
    medication_id: str
    event_date: str
    scheduled_time: str
    status: str
    taken_at: str | None
    note: str | None
    created_at: str


def _to_resp(r):
    return CalendarEventResponse(
        id=str(r.id),
        medication_id=str(r.medication_id),
        event_date=str(r.event_date),
        scheduled_time=str(r.scheduled_time),
        status=r.status,
        taken_at=str(r.taken_at) if r.taken_at else None,
        note=r.note,
        created_at=str(r.created_at),
    )


@calendar_router.get("", summary="List monthly calendar")
async def list_calendar_month(year: str = Query(...), month: str = Query(...), current_user=Depends(get_request_user)):
    y, m = int(year), int(month)
    first_day = date(y, m, 1)
    last_day = date(y, m + 1, 1) if m < 12 else date(y + 1, 1, 1)
    rows = await CalendarEvent.filter(
        user_id=current_user.id,
        event_date__gte=first_day,
        event_date__lt=last_day,
    ).order_by("event_date", "scheduled_time")
    return _ok({"year": y, "month": m, "total": len(rows), "items": [_to_resp(r) for r in rows]})


@calendar_router.get("/{event_date}", summary="List daily calendar")
async def get_calendar_by_date(event_date: str, current_user=Depends(get_request_user)):
    rows = await CalendarEvent.filter(user_id=current_user.id, event_date=event_date).order_by("scheduled_time")
    return _ok([_to_resp(r) for r in rows])


@calendar_router.post("", summary="Create calendar event", status_code=status.HTTP_201_CREATED)
async def create_calendar_event(body: CalendarEventCreateRequest, current_user=Depends(get_request_user)):
    from app.models.medical_records import MedicalRecord
    from app.models.medications import Medication
    from app.models.notifications import Notification

    med = await Medication.filter(id=body.medication_id).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found.")
    record = await MedicalRecord.filter(id=med.medical_record_id, user_id=current_user.id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found.")
    duplicate = await CalendarEvent.filter(
        user_id=current_user.id,
        medication_id=body.medication_id,
        event_date=body.event_date,
        scheduled_time=body.scheduled_time,
    ).exists()
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 같은 시간에 해당 약의 복약 일정이 존재합니다.")
    row = await CalendarEvent.create(
        user_id=current_user.id,
        medication_id=body.medication_id,
        event_date=body.event_date,
        scheduled_time=body.scheduled_time,
        status="PENDING",
        note=body.note,
    )
    exists = await Notification.filter(
        user_id=current_user.id,
        medication_id=body.medication_id,
        scheduled_time=body.scheduled_time,
    ).exists()
    if not exists:
        await Notification.create(
            user_id=current_user.id,
            medication_id=body.medication_id,
            title=f"{med.drug_name} 복용 알림",
            type="push",
            scheduled_time=body.scheduled_time,
            is_active=True,
        )
    return _ok(_to_resp(row))


@calendar_router.put("/{event_id}/status", summary="Update event status")
async def update_calendar_status(
    event_id: str, body: CalendarStatusUpdateRequest, current_user=Depends(get_request_user)
):
    row = await CalendarEvent.filter(id=event_id, user_id=current_user.id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar event not found.")
    row.status = body.status
    if body.status == "TAKEN":
        row.taken_at = datetime.now(UTC)
    await row.save(update_fields=["status", "taken_at"])
    return _ok(_to_resp(row))


class CalendarTimeUpdateRequest(BaseModel):
    scheduled_time: str = Field(..., description="HH:MM:SS")


@calendar_router.patch("/{event_id}/time", summary="Update event scheduled time")
async def update_calendar_time(event_id: str, body: CalendarTimeUpdateRequest, current_user=Depends(get_request_user)):
    row = await CalendarEvent.filter(id=event_id, user_id=current_user.id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar event not found.")
    row.scheduled_time = body.scheduled_time
    await row.save(update_fields=["scheduled_time"])
    return _ok(_to_resp(row))


@calendar_router.delete("/{event_id}", summary="Delete calendar event")
async def delete_calendar_event(event_id: str, current_user=Depends(get_request_user)):
    deleted = await CalendarEvent.filter(id=event_id, user_id=current_user.id).delete()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar event not found.")
    return _ok({"message": "Deleted."})
