from tortoise import fields, models


class Guide(models.Model):
    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="guides")
    medical_record = fields.ForeignKeyField("models.MedicalRecord", related_name="guides")
    status = fields.CharField(max_length=20, default="processing")
    medication_guide = fields.TextField(null=True)
    lifestyle_guide = fields.TextField(null=True)
    summary_text = fields.TextField(null=True)
    allergy_warnings = fields.JSONField(null=True)
    condition_interactions = fields.JSONField(null=True)
    prompt_version = fields.CharField(max_length=20, default="v1.0")
    llm_model = fields.CharField(max_length=100, null=True)
    llm_temperature = fields.FloatField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "guides"