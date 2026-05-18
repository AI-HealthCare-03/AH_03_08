# app/dtos/image.py

# 서드파티 라이브러리
from pydantic import BaseModel


# Response DTO: 분석 요청 후 즉시 반환되는 데이터 (202 Accepted)
class ImageAnalyzeResponse(BaseModel):
    analysis_id: str  # 생성된 분석 작업 ID
    status: str       # "processing" (Celery 작업 등록 완료)


# Response DTO: 결과 조회 응답 (GET /api/v1/images/{analysis_id})
class DrugInfoResponse(BaseModel):
    analysis_id: str
    status: str                    # "processing" or "completed"
    drug_name: str | None = None
    dl_material: str | None = None
    drug_shape: str | None = None
    color_class1: str | None = None
    di_class_no: str | None = None
    di_etc_otc_code: str | None = None
    confidence_score: float | None = None
    disclaimer: str | None = "본 정보는 참고용이며, 정확한 복약 정보는 전문가에게 확인하세요."