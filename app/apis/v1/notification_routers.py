# app/apis/v1/notification_routers.py
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
    is_active: bool


class NotificationResponse(BaseModel):
    id: str
    medication_id: str
    title: str
    type: str
    scheduled_time: str
    is_active: bool
    created_at: str


@notification_router.get("", summary="List notifications")
async def list_notifications(current_user=Depends(get_request_user)):
    rows = await Notification.filter(user_id=current_user.id).order_by("scheduled_time")
    return _ok(
        [
            NotificationResponse(
                id=str(r.id),
                medication_id=str(r.medication_id),
                title=r.title,
                type=r.type,
                scheduled_time=str(r.scheduled_time),
                is_active=r.is_active,
                created_at=str(r.created_at),
            )
            for r in rows
        ]
    )


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
    row.is_active = body.is_active
    await row.save(update_fields=["is_active"])
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
    deleted = await Notification.filter(id=notification_id, user_id=current_user.id).delete()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return _ok({"message": "Deleted."})
