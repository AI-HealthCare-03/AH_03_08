from enum import IntEnum, StrEnum

from tortoise import fields, models


class RecordType(IntEnum):
    PRESCRIPTION = 0
    DRUG_BAG = 1
    PILL = 2


class RecordStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class GuideStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class AssetType(StrEnum):
    TTS = "TTS"
    CARD_IMAGE = "CARD_IMAGE"


# ════════════════════════════════════════
# Guide 모델
# ════════════════════════════════════════


class Guide(models.Model):
    """복약 가이드

    ✅ [변경] medication_guide, lifestyle_guide 타입 변경
    ─────────────────────────────────────────────────────
    기존: TextField (문자열 덩어리)
          - 프론트에서 약품별 파싱 불가
          - 구조 변경 시 모든 클라이언트 파싱 로직 수정 필요

    개선: JSONField (구조화된 dict/list)
          - medication_guide → list[dict]: 약품별 카드 UI, TTS 분리, 알림 설정 가능
          - lifestyle_guide  → dict:       diet/exercise/sleep/other 섹션 분리
          - null=True: PENDING/PROCESSING 상태에서 빈 값 허용

    마이그레이션 SQL (MySQL 기준):
    ─────────────────────────────────────────────────────
        ALTER TABLE guides
            MODIFY COLUMN medication_guide JSON NULL,
            MODIFY COLUMN lifestyle_guide  JSON NULL;

        -- 기존 데이터가 있다면 NULL로 초기화 후 재생성 권장:
        UPDATE guides SET medication_guide = NULL, lifestyle_guide = NULL
        WHERE status != 'done';
    ─────────────────────────────────────────────────────
    """

    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="guides", on_delete=fields.CASCADE)
    record = fields.ForeignKeyField("models.MedicalRecord", related_name="guides", on_delete=fields.CASCADE)

    status = fields.CharField(max_length=20, default=GuideStatus.PENDING)

    # ✅ TextField → JSONField
    medication_guide: list[dict] | None = fields.JSONField(null=True)
    lifestyle_guide: dict | None = fields.JSONField(null=True)

    summary_text = fields.TextField(null=True)

    # 기존과 동일 — 이미 JSON 저장 중
    allergy_warnings: list[dict] = fields.JSONField(default=list)
    condition_interactions: list[dict] = fields.JSONField(default=list)

    llm_model = fields.CharField(max_length=50, null=True)
    llm_temperature = fields.FloatField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "guides"


# ════════════════════════════════════════
# MedicalRecord 모델
# ════════════════════════════════════════


class MedicalRecord(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="records", on_delete=fields.CASCADE)
    record_type = fields.IntEnumField(RecordType)
    status = fields.CharEnumField(RecordStatus, default=RecordStatus.PENDING)
    file_url = fields.CharField(max_length=500, null=True)
    parsed_data: dict | None = fields.JSONField(null=True)  # OCR 결과
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "medical_records"


# ════════════════════════════════════════
# GuideAsset 모델
# ════════════════════════════════════════


class GuideAsset(models.Model):
    id = fields.UUIDField(primary_key=True)
    guide = fields.ForeignKeyField("models.Guide", related_name="assets", on_delete=fields.CASCADE)
    asset_type = fields.CharField(max_length=50)
    file_url = fields.CharField(max_length=500, null=True)
    status = fields.CharField(max_length=20, default="PENDING")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "guide_assets"


# ════════════════════════════════════════
# Chat 모델
# ════════════════════════════════════════


class ChatSession(models.Model):
    id = fields.BigIntField(primary_key=True, generated=True)
    user = fields.ForeignKeyField("models.User", related_name="chat_sessions", on_delete=fields.CASCADE)
    guide = fields.ForeignKeyField("models.Guide", related_name="chat_sessions", on_delete=fields.CASCADE, null=True)
    title = fields.CharField(max_length=200, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "chat_sessions"


class ChatMessage(models.Model):
    id = fields.BigIntField(primary_key=True, generated=True)
    session = fields.ForeignKeyField("models.ChatSession", related_name="messages", on_delete=fields.CASCADE)
    role = fields.CharField(max_length=10)
    content = fields.TextField(default="")
    status = fields.CharField(max_length=20, default="DONE")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chat_messages"
        ordering = ["created_at"]
