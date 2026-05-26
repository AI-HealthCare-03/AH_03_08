# app/apis/v1/image_routers.py
# 표준 라이브러리
from typing import Annotated

# 서드파티 라이브러리
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse as Response

# 로컬 모듈
from app.dependencies.security import get_request_user
from app.dtos.image import DrugInfoResponse
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
    return Response(
        content=DrugInfoResponse(
            record_id=record_id,
            status=record.status,
            drug_name=parsed_data.get("drug_name"),
            dl_company=parsed_data.get("dl_company"),
            dl_material=parsed_data.get("dl_material"),
            drug_shape=parsed_data.get("drug_shape"),
            color_class1=parsed_data.get("color_class1"),
            di_class_no=parsed_data.get("di_class_no"),
            di_etc_otc_code=parsed_data.get("di_etc_otc_code"),
            chart=parsed_data.get("chart"),
            print_front=parsed_data.get("print_front"),
            print_back=parsed_data.get("print_back"),
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )