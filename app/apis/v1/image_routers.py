# app/apis/v1/image_routers.py

# 표준 라이브러리
import json
from typing import Annotated

# 서드파티 라이브러리
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse as Response

# 로컬 모듈
from app.core.config import config
from app.dependencies.security import get_request_user
from app.dtos.image import DrugInfoResponse, PillMatchRequest, PillMatchResponse
from app.models.medical_records import MedicalRecord
from app.models.users import User

image_router = APIRouter(prefix="/images", tags=["images"])


@image_router.get(
    "/{record_id}",
    response_model=DrugInfoResponse,
    status_code=status.HTTP_200_OK,
)
async def get_analysis_result(
    record_id: str,
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """
    낱알약 이미지 분류 결과 조회 엔드포인트.
    REQ-IMG-006, REQ-IMG-007 연동
    Args:
        record_id: 분류 작업 record_id
        current_user: JWT 인증된 사용자 (Bearer token)
    Returns:
        200 OK: { record_id, status, drug_info... }
    Note:
        - 개인정보 보호: 본인 소유 진료기록만 조회 가능
    """
    record = await MedicalRecord.get_or_none(id=record_id, user_id=current_user.id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료기록을 찾을 수 없습니다.")
    parsed_data = record.parsed_data or {}
    drug_info = parsed_data.get("drug_info", {})
    return Response(
        content=DrugInfoResponse(
            record_id=record_id,
            status=record.status,
            drug_name=drug_info.get("drug_name"),
            dl_company=drug_info.get("dl_company"),
            dl_material=drug_info.get("dl_material"),
            drug_shape=drug_info.get("drug_shape"),
            color_class1=drug_info.get("color_class1"),
            di_class_no=drug_info.get("di_class_no"),
            di_etc_otc_code=drug_info.get("di_etc_otc_code"),
            chart=drug_info.get("chart"),
            print_front=drug_info.get("print_front"),
            print_back=drug_info.get("print_back"),
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@image_router.post(
    "/pill-match",
    response_model=PillMatchResponse,
    status_code=status.HTTP_200_OK,
)
async def match_pill_by_ocr(
    request: PillMatchRequest,
    current_user: Annotated[User, Depends(get_request_user)],
) -> PillMatchResponse:
    """
    OCR 식별코드로 약품 매칭 엔드포인트.
    사용자가 식별코드 수정 후 재매칭 시 사용.
    """
    try:
        with open(config.PILL_PRINT_INDEX_PATH, encoding="utf-8") as f:
            index_data = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="인덱스 파일을 불러올 수 없습니다.",
        ) from e

    print_index = index_data.get("print_index", {})
    kcode_info = index_data.get("kcode_info", {})

    candidates: dict[str, int] = {}
    for text in request.ocr_texts:
        text_upper = text.strip().upper()
        if text_upper in print_index:
            for kcode in print_index[text_upper]:
                candidates[kcode] = candidates.get(kcode, 0) + 1

    if not candidates:
        return PillMatchResponse(matched=False)

    best_kcode = max(candidates, key=lambda k: candidates[k])
    info = kcode_info.get(best_kcode)
    if not info:
        return PillMatchResponse(matched=False)

    return PillMatchResponse(
        matched=True,
        kcode=best_kcode,
        drug_name=info.get("dl_name"),
        dl_material=info.get("dl_material"),
        di_class_no=info.get("di_class_no"),
        di_etc_otc_code=info.get("di_etc_otc_code"),
        print_front=info.get("print_front"),
        print_back=info.get("print_back"),
    )
