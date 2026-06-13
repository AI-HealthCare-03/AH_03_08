import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse as Response

from app.core.config import config
from app.dependencies.security import get_request_user
from app.dtos.health import (
    AllergyRequest,
    AllergyResponse,
    DrugSearchItem,
    MedicalRecordCreateRequest,
    MedicalRecordResponse,
    MedicationCreateRequest,
    MedicationResponse,
    UnderlyingDiseaseRequest,
    UnderlyingDiseaseResponse,
)
from app.models.users import User
from app.services.health import HealthService

logger = logging.getLogger(__name__)

_DRUG_API_URL = "https://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07"

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


@health_router.get("/medications", response_model=list[MedicationResponse], status_code=status.HTTP_200_OK)
async def get_medications(
    user: Annotated[User, Depends(get_request_user)],
    health_service: Annotated[HealthService, Depends(HealthService)],
) -> Response:
    medications = await health_service.get_medications(user=user)
    return Response([MedicationResponse.model_validate(m).model_dump() for m in medications])


@health_router.get("/medications/drug-search", response_model=list[DrugSearchItem], status_code=status.HTTP_200_OK)
async def search_drug(
    q: Annotated[str, Query(min_length=1, max_length=100)],
    _: Annotated[User, Depends(get_request_user)],
) -> Response:
    if not config.PUBLIC_DATA_API_KEY:
        return Response([])
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                _DRUG_API_URL,
                params={"serviceKey": config.PUBLIC_DATA_API_KEY, "item_name": q, "numOfRows": "8", "pageNo": "1", "type": "json"},
            )
            items = (resp.json().get("body") or {}).get("items") or []
            # 결과 없거나 drug_class 없으면 캅셀↔캡슐 표기 변환 후 재검색
            no_class = items and not any(item.get("PRDUCT_TYPE") for item in items)
            if not items or no_class:
                if "캅셀" in q:
                    q2 = q.replace("캅셀", "캡슐")
                elif "캡슐" in q:
                    q2 = q.replace("캡슐", "캅셀")
                else:
                    q2 = None
                if q2:
                    resp2 = await client.get(
                        _DRUG_API_URL,
                        params={"serviceKey": config.PUBLIC_DATA_API_KEY, "item_name": q2, "numOfRows": "8", "pageNo": "1", "type": "json"},
                    )
                    items2 = (resp2.json().get("body") or {}).get("items") or []
                    if items2:
                        items = items2
        results = []
        seen = set()
        for item in items:
            name = (item.get("ITEM_NAME") or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            raw_class = item.get("PRDUCT_TYPE") or ""
            drug_class = raw_class.split("]")[-1].strip() if "]" in raw_class else raw_class or None
            results.append(DrugSearchItem(
                drug_name=name,
                drug_class=drug_class or None,
                dosage=None,
            ))
        return Response([r.model_dump() for r in results])
    except Exception as e:
        logger.warning(f"[drug-search] 실패: {e}")
        return Response([])


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
