from tortoise import fields, models


class Guide(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="guides")
    medical_record = fields.ForeignKeyField("models.MedicalRecord", related_name="guides")
    medication_guide = fields.TextField(null=True)    # 복약 안내
    lifestyle_guide = fields.TextField(null=True)     # 생활습관 안내
    llm_model = fields.CharField(max_length=100, null=True)
    llm_temperature = fields.FloatField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "guides"