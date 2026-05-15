from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.health import AIAnalysisRequest, GuideResponse
from app.models.users import User
from app.services.ai_service import AIService
from app.services.health import HealthService

ai_router = APIRouter(prefix="/ai", tags=["ai"])


@ai_router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def request_ai_analysis(
    data: AIAnalysisRequest,
    user: Annotated[User, Depends(get_request_user)],
    health_service: Annotated[HealthService, Depends(HealthService)],
    ai_service: Annotated[AIService, Depends(AIService)],
) -> Response:
    record = await health_service.get_record_or_404(record_id=data.medical_record_id, user=user)
    guide, task_id = await ai_service.request_analysis(user=user, medical_record=record)
    return Response(
        content={
            "detail": "분석 요청이 접수됐습니다.",
            "guide_id": str(guide.id),
            "celery_task_id": task_id,
        },
        status_code=status.HTTP_202_ACCEPTED,
    )


@ai_router.get("/guides/{guide_id}", response_model=GuideResponse, status_code=status.HTTP_200_OK)
async def get_guide(
    guide_id: str,
    user: Annotated[User, Depends(get_request_user)],
    ai_service: Annotated[AIService, Depends(AIService)],
) -> Response:
    guide = await ai_service.get_guide_or_404(guide_id=guide_id, user=user)
    return Response(GuideResponse.model_validate(guide).model_dump())