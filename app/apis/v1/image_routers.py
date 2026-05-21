# app/apis/v1/image_routers.py
# 표준 라이브러리
from typing import Annotated
from uuid import UUID

# 서드파티 라이브러리
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import JSONResponse as Response

# 로컬 모듈
from app.dependencies.security import get_request_user
from app.dtos.image import DrugInfoResponse, ImageAnalyzeResponse
from app.models.users import User
from app.services.image import ImageService

image_router = APIRouter(prefix="/images", tags=["images"])


@image_router.post(
    "/analyze",
    response_model=ImageAnalyzeResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_image(
    record_id: Annotated[str, Form()],
    image: Annotated[UploadFile, File()],
    image_service: Annotated[ImageService, Depends(ImageService)],
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """
    낱알약 이미지 분류 요청 엔드포인트.
    API 명세서: POST /api/v1/images/analyze
    REQ-IMG-001 ~ REQ-IMG-005 연동
    Args:
        record_id: 여진님 /records/upload에서 반환된 record_id
        current_user: JWT 인증된 사용자 (Bearer token)
    Returns:
        202 Accepted: { analysis_id, status: "processing" }
    Note:
        - 개인정보 보호: 의료 데이터 접근 시 JWT 인증 필수
        - 파일 업로드는 POST /api/v1/records/upload에서 처리
        - Celery Task 등록 후 즉시 202 반환 (비동기 처리)
    """
    image_bytes = await image.read()
    result = await image_service.analyze_image(
        record_id=record_id,
        user_id=str(current_user.id),
        image_bytes=image_bytes,
)
    return Response(
        content=result.model_dump(),
        status_code=status.HTTP_202_ACCEPTED,
    )


@image_router.get(
    "/{analysis_id}",
    response_model=DrugInfoResponse,
    status_code=status.HTTP_200_OK,
)
async def get_analysis_result(
    analysis_id: UUID,
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """
    낱알약 이미지 분류 결과 조회 엔드포인트.
    API 명세서: GET /api/v1/images/{analysis_id}
    REQ-IMG-006, REQ-IMG-007 연동
    Args:
        analysis_id: 분류 작업 고유 ID
        current_user: JWT 인증된 사용자 (Bearer token)
    Returns:
        200 OK: { analysis_id, status, drug_info... }
    Note:
        - 개인정보 보호: 의료 데이터 접근 시 JWT 인증 필수
        - TODO: 팀장님 feature/db-models-and-api merge 후 DB 조회 연동 예정
    """
    return Response(
        content=DrugInfoResponse(
            analysis_id=str(analysis_id),
            status="processing",
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )
