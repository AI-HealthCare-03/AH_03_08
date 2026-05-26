from tortoise import fields, models


class Guide(models.Model):
    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="guides")
    # DB 컬럼명 record_id (medical_records FK)
    record = fields.ForeignKeyField("models.MedicalRecord", related_name="guides", source_field="record_id")
    status = fields.CharField(max_length=20, default="processing")  # processing / done / failed
    title = fields.CharField(max_length=200, null=True)
    medication_guide = fields.TextField(null=True)
    lifestyle_guide = fields.TextField(null=True)
    summary_text = fields.TextField(null=True)
    allergy_warnings = fields.JSONField(default=list)
    condition_interactions = fields.JSONField(default=list)
    prompt_version = fields.CharField(max_length=20, default="v1.0")
    llm_model = fields.CharField(max_length=100, null=True)
    llm_temperature = fields.FloatField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "guides"
