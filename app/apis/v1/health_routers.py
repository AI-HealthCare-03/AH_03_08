from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.health import (
    MedicalRecordCreateRequest, MedicalRecordResponse,
    MedicationCreateRequest, MedicationResponse,
    UnderlyingDiseaseRequest, UnderlyingDiseaseResponse,
    AllergyRequest, AllergyResponse,
)
from app.models.users import User
from app.services.health import HealthService

health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.post("/records", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_medical_record(
    data: MedicalRecordCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    health_service: Annotated[HealthService, Depends(HealthService)],
) -> Response:
    record = await health_service.create_record(user=user, data=data)
    return Response(MedicalRecordResponse.model_validate(record).model_dump(), status_code=status.HTTP_201_CREATED)


@health_router.get("/records", response_model=list[MedicalRecordResponse], status_code=status.HTTP_200_OK)
async def get_medical_records(
    user: Annotated[User, Depends(get_request_user)],
    health_service: Annotated[HealthService, Depends(HealthService)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Response:
    records = await health_service.get_records(user=user, limit=limit, offset=offset)
    return Response([MedicalRecordResponse.model_validate(r).model_dump() for r in records])


@health_router.post("/medications", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
async def create_medication(
    data: MedicationCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    health_service: Annotated[HealthService, Depends(HealthService)],
) -> Response:
    medication = await health_service.create_medication(user=user, data=data)
    return Response(MedicationResponse.model_validate(medication).model_dump(), status_code=status.HTTP_201_CREATED)


@health_router.post("/diseases", response_model=UnderlyingDiseaseResponse, status_code=status.HTTP_201_CREATED)
async def create_disease(
    data: UnderlyingDiseaseRequest,
    user: Annotated[User, Depends(get_request_user)],
    health_service: Annotated[HealthService, Depends(HealthService)],
) -> Response:
    disease = await health_service.create_disease(user=user, data=data)
    return Response(UnderlyingDiseaseResponse.model_validate(disease).model_dump(), status_code=status.HTTP_201_CREATED)


@health_router.get("/diseases", response_model=list[UnderlyingDiseaseResponse], status_code=status.HTTP_200_OK)
async def get_diseases(
    user: Annotated[User, Depends(get_request_user)],
    health_service: Annotated[HealthService, Depends(HealthService)],
) -> Response:
    diseases = await health_service.get_diseases(user=user)
    return Response([UnderlyingDiseaseResponse.model_validate(d).model_dump() for d in diseases])


@health_router.delete("/diseases/{disease_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_disease(
    disease_id: str,
    user: Annotated[User, Depends(get_request_user)],
    health_service: Annotated[HealthService, Depends(HealthService)],
) -> None:
    await health_service.delete_disease(disease_id=disease_id, user=user)


@health_router.post("/allergies", response_model=AllergyResponse, status_code=status.HTTP_201_CREATED)
async def create_allergy(
    data: AllergyRequest,
    user: Annotated[User, Depends(get_request_user)],
    health_service: Annotated[HealthService, Depends(HealthService)],
) -> Response:
    allergy = await health_service.create_allergy(user=user, data=data)
    return Response(AllergyResponse.model_validate(allergy).model_dump(), status_code=status.HTTP_201_CREATED)


@health_router.get("/allergies", response_model=list[AllergyResponse], status_code=status.HTTP_200_OK)
async def get_allergies(
    user: Annotated[User, Depends(get_request_user)],
    health_service: Annotated[HealthService, Depends(HealthService)],
) -> Response:
    allergies = await health_service.get_allergies(user=user)
    return Response([AllergyResponse.model_validate(a).model_dump() for a in allergies])


@health_router.delete("/allergies/{allergy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_allergy(
    allergy_id: str,
    user: Annotated[User, Depends(get_request_user)],
    health_service: Annotated[HealthService, Depends(HealthService)],
) -> None:
    await health_service.delete_allergy(allergy_id=allergy_id, user=user)