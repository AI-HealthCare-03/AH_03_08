# app/apis/v1/user_routers.py
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies.security import get_request_user
from app.models.allergies import Allergy
from app.models.underlying_diseases import UnderlyingDisease

user_router = APIRouter(prefix="/users", tags=["users"])


def _ok(data):
    return {"success": True, "data": data, "message": "ok"}


class AllergyCreateRequest(BaseModel):
    allergen_name: str = Field(..., max_length=200)
    severity: Literal["mild", "moderate", "severe"] = "mild"


class AllergyResponse(BaseModel):
    id: str
    allergen_name: str
    severity: str
    created_at: str


class ConditionCreateRequest(BaseModel):
    condition_name: str = Field(..., max_length=200)
    severity: Literal["mild", "moderate", "severe"] = "mild"


class ConditionResponse(BaseModel):
    id: str
    condition_name: str
    severity: str
    created_at: str


@user_router.get("/me/allergies", summary="알러지 목록 조회")
async def list_my_allergies(current_user=Depends(get_request_user)):
    rows = await Allergy.filter(user_id=current_user.id).order_by("created_at")
    return _ok(
        [
            AllergyResponse(
                id=str(r.id), allergen_name=r.allergy_name, severity=r.severity or "mild", created_at=str(r.created_at)
            )
            for r in rows
        ]
    )


@user_router.post("/me/allergies", summary="알러지 추가", status_code=status.HTTP_201_CREATED)
async def add_my_allergy(body: AllergyCreateRequest, current_user=Depends(get_request_user)):
    row = await Allergy.create(user_id=current_user.id, allergy_name=body.allergen_name, severity=body.severity)
    return _ok(
        AllergyResponse(
            id=str(row.id),
            allergen_name=row.allergy_name,
            severity=row.severity or "mild",
            created_at=str(row.created_at),
        )
    )


@user_router.delete("/me/allergies/{allergy_id}", summary="알러지 삭제")
async def delete_my_allergy(allergy_id: str, current_user=Depends(get_request_user)):
    deleted = await Allergy.filter(id=allergy_id, user_id=current_user.id).delete()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="알러지 정보를 찾을 수 없습니다.")
    return _ok({"message": "삭제 완료"})


@user_router.get("/me/conditions", summary="기저질환 목록 조회")
async def list_my_conditions(current_user=Depends(get_request_user)):
    rows = await UnderlyingDisease.filter(user_id=current_user.id).order_by("created_at")
    return _ok(
        [
            ConditionResponse(
                id=str(r.id),
                condition_name=r.underlying_disease_name,
                severity=r.severity or "mild",
                created_at=str(r.created_at),
            )
            for r in rows
        ]
    )


@user_router.post("/me/conditions", summary="기저질환 추가", status_code=status.HTTP_201_CREATED)
async def add_my_condition(body: ConditionCreateRequest, current_user=Depends(get_request_user)):
    row = await UnderlyingDisease.create(
        user_id=current_user.id, underlying_disease_name=body.condition_name, severity=body.severity
    )
    return _ok(
        ConditionResponse(
            id=str(row.id),
            condition_name=row.underlying_disease_name,
            severity=row.severity or "mild",
            created_at=str(row.created_at),
        )
    )


@user_router.delete("/me/conditions/{condition_id}", summary="기저질환 삭제")
async def delete_my_condition(condition_id: str, current_user=Depends(get_request_user)):
    deleted = await UnderlyingDisease.filter(id=condition_id, user_id=current_user.id).delete()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="기저질환 정보를 찾을 수 없습니다.")
    return _ok({"message": "삭제 완료"})


class UserMeResponse(BaseModel):
    id: int
    email: str
    name: str
    gender: str | None = None
    birth_date: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None


class UserMeUpdateRequest(BaseModel):
    name: str | None = None
    gender: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None


@user_router.get("/me", summary="Get my profile")
async def get_my_profile(current_user=Depends(get_request_user)):
    return _ok(
        UserMeResponse(
            id=current_user.id,
            email=current_user.email,
            name=current_user.name,
            gender=current_user.gender if hasattr(current_user, "gender") else None,
            birth_date=str(current_user.birth_date) if getattr(current_user, "birth_date", None) else None,
            height_cm=getattr(current_user, "height_cm", None),
            weight_kg=getattr(current_user, "weight_kg", None),
        )
    )


@user_router.patch("/me", summary="Update my profile")
async def update_my_profile(
    body: UserMeUpdateRequest,
    current_user=Depends(get_request_user),
):
    update_fields = []
    if body.name is not None:
        current_user.name = body.name
        update_fields.append("name")
    if body.gender is not None:
        current_user.gender = body.gender
        update_fields.append("gender")
    if body.height_cm is not None:
        current_user.height_cm = body.height_cm
        update_fields.append("height_cm")
    if body.weight_kg is not None:
        current_user.weight_kg = body.weight_kg
        update_fields.append("weight_kg")
    if update_fields:
        await current_user.save(update_fields=update_fields)
    return _ok({"message": "Updated."})
