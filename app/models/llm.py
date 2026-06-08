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
