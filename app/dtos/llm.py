from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel
from app.models.llm import AssetType, GuideStatus, RecordStatus, RecordType

# ════════════════════════════════════════
# MedicalRecord DTOs
# ════════════════════════════════════════


class RecordCreateRequest(BaseModel):
    """처방전/약봉투 레코드 생성 요청"""

    record_type: RecordType
    file_url: Annotated[str | None, Field(None, max_length=500)]


class RecordResponse(BaseSerializerModel):
    """레코드 응답 — ORM 객체 직렬화"""

    id: UUID
    record_type: RecordType
    status: RecordStatus
    file_url: str | None
    created_at: datetime


class RecordListResponse(BaseModel):
    """레코드 목록 응답"""

    total: int
    page: int
    items: list[RecordResponse]


# ════════════════════════════════════════
# Guide DTOs
# ════════════════════════════════════════


class GuideGenerateRequest(BaseModel):
    """가이드 생성 요청 — OCR 완료된 record_id 전달"""

    record_id: UUID


class GuideGenerateResponse(BaseModel):
    """가이드 생성 응답 — 즉시 202 반환, LLM은 백그라운드에서 처리"""

    guide_id: UUID
    status: GuideStatus  # 항상 PENDING으로 시작


# ✅ [신규] 복약 가이드 개별 약품 항목
# 기존: medication_guide가 str 단일 필드 → 프론트 파싱 불가, 약품별 UI 불가
# 개선: 약품별 구조화 객체 → 카드 UI 렌더링, TTS 분리, 개별 알림 설정 가능
class MedicationGuideItem(BaseModel):
    """약품별 복약 가이드 항목"""

    drug_name: str
    how_to_take: str                       # 복용 방법 (예: 식후 30분, 물과 함께)
    schedule: str                          # 복용 시간대 (예: 아침·저녁 식후)
    warnings: list[str] = Field(default_factory=list)      # 주의사항 목록
    side_effects: list[str] = Field(default_factory=list)  # 흔한 부작용 목록


# ✅ [신규] 생활습관 가이드 카테고리 분리
# 기존: lifestyle_guide가 str 단일 필드 → 식이/운동/수면 섹션 구분 불가
# 개선: 카테고리별 필드 분리 → 프론트에서 탭/섹션 UI 구성 가능
class LifestyleGuide(BaseModel):
    """생활습관 가이드 (카테고리별)"""

    diet: str | None = None      # 식이 권고사항
    exercise: str | None = None  # 운동 관련 주의사항
    sleep: str | None = None     # 수면 관련 안내
    other: str | None = None     # 기타 생활습관 개선사항


class AllergyWarning(BaseModel):
    """알러지 경고 항목"""

    drug_name: str
    warning: str


class ConditionInteraction(BaseModel):
    """기저질환 상호작용 항목"""

    drug_name: str
    condition: str
    interaction: str


class GuideDetailResponse(BaseSerializerModel):
    """가이드 상세 응답

    ✅ [변경]
    - medication_guide: str → list[MedicationGuideItem]
    - lifestyle_guide:  str → LifestyleGuide
    """

    id: UUID
    status: GuideStatus

    # ✅ 구조화된 타입으로 변경 (None 허용: PENDING/PROCESSING 상태 대응)
    medication_guide: list[MedicationGuideItem] | None = None
    lifestyle_guide: LifestyleGuide | None = None

    summary_text: str | None
    allergy_warnings: list[AllergyWarning]
    condition_interactions: list[ConditionInteraction]
    created_at: datetime


class GuideListItem(BaseSerializerModel):
    """가이드 목록 항목"""

    id: UUID
    status: GuideStatus
    created_at: datetime


class GuideListResponse(BaseModel):
    """가이드 목록 응답"""

    total: int
    page: int
    items: list[GuideListItem]


# ════════════════════════════════════════
# GuideAsset DTOs
# ════════════════════════════════════════


class AssetCreateRequest(BaseModel):
    """에셋 생성 요청 — TTS 음성 or 카드뉴스 이미지"""

    asset_type: AssetType


class AssetCreateResponse(BaseModel):
    """에셋 생성 응답 — 즉시 202 반환, Worker가 백그라운드에서 생성"""

    asset_id: UUID
    status: RecordStatus  # 항상 PENDING으로 시작


class AssetDetailResponse(BaseSerializerModel):
    """에셋 상세 응답"""

    id: UUID
    asset_type: AssetType
    file_url: str | None  # 생성 완료 후 S3 URL 저장
    status: RecordStatus
    created_at: datetime


# ════════════════════════════════════════
# ChatSession DTOs
# ════════════════════════════════════════


class ChatSessionResponse(BaseSerializerModel):
    """챗봇 세션 응답 — ws_url로 바로 WebSocket 연결 가능"""

    id: int
    created_at: datetime
    ws_url: str


class ChatSessionListResponse(BaseModel):
    """챗봇 세션 목록 응답"""

    sessions: list[ChatSessionResponse]


# ════════════════════════════════════════
# ChatMessage DTOs
# ════════════════════════════════════════


class ChatMessageSendRequest(BaseModel):
    """메시지 전송 요청"""

    message: Annotated[str, Field(min_length=1, max_length=2000)]


class ChatMessageResponse(BaseSerializerModel):
    """메시지 응답"""

    id: int
    role: str  # user | assistant
    content: str
    status: RecordStatus
    created_at: datetime


class ChatMessageListResponse(BaseModel):
    """대화 내역 응답 — 커서 기반 페이지네이션"""

    messages: list[ChatMessageResponse]
    next_cursor: int | None  # 다음 요청 시 ?cursor=값 으로 사용