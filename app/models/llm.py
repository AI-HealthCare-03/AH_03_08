from enum import IntEnum, StrEnum

from tortoise import fields, models


class RecordType(IntEnum):
    PRESCRIPTION = 0
    DRUG_BAG = 1
    PILL = 2


class RecordStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"  # DONE → COMPLETED
    FAILED = "FAILED"


class GuideStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class AssetType(StrEnum):
    TTS = "TTS"
    CARD_IMAGE = "CARD_IMAGE"


class GuideAsset(models.Model):
    id = fields.UUIDField(primary_key=True)
    guide = fields.ForeignKeyField("models.Guide", related_name="assets", on_delete=fields.CASCADE)
    asset_type = fields.CharField(max_length=50)
    file_url = fields.CharField(max_length=500, null=True)
    status = fields.CharField(max_length=20, default="PENDING")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "guide_assets"


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
