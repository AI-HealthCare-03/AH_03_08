from tortoise import fields
from tortoise.models import Model


class Guide(Model):
    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="guides", on_delete=fields.CASCADE)
    record = fields.ForeignKeyField(
        "models.MedicalRecord",
        related_name="guides",
        source_field="record_id",
        on_delete=fields.CASCADE,
    )
    status = fields.CharField(max_length=20, default="processing")
    title = fields.CharField(max_length=200, null=True)
    medication_guide = fields.JSONField(null=True)
    lifestyle_guide = fields.JSONField(null=True)
    summary_text = fields.TextField(null=True)
    allergy_warnings = fields.JSONField(default=list)
    condition_interactions = fields.JSONField(default=list)
    drug_interactions = fields.JSONField(default=list)
    side_effects_watch = fields.JSONField(default=list)
    medication_schedule = fields.JSONField(default=list)
    urgent_warnings = fields.JSONField(default=list)
    prompt_version = fields.CharField(max_length=20, default="v1.0")
    llm_model = fields.CharField(max_length=100, null=True)
    llm_temperature = fields.FloatField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "guides"


class Feedback(Model):
    id = fields.UUIDField(pk=True)
    guide_id = fields.UUIDField()
    user_id = fields.UUIDField()
    rating = fields.IntField(null=True)
    comment = fields.CharField(max_length=500, null=True)
    status = fields.CharField(max_length=20, null=True)
    deactive_at = fields.DatetimeField(null=True)
    deactive_by = fields.UUIDField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "feedbacks"
