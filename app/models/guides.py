from tortoise import fields, models


class Guide(models.Model):
    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="guides")
    medical_record = fields.ForeignKeyField("models.MedicalRecord", related_name="guides")
    status = fields.CharField(max_length=20, default="processing")  # processing / done / failed
    medication_guide = fields.TextField(null=True)  # 복약 안내
    lifestyle_guide = fields.TextField(null=True)  # 생활습관 안내
    summary_text = fields.TextField(null=True)  # 전체 요약
    allergy_warnings = fields.JSONField(null=True)  # 알러지 경고 목록
    condition_interactions = fields.JSONField(null=True)  # 기저질환 상호작용
    prompt_version = fields.CharField(max_length=20, default="v1.0")  # 프롬프트 버전
    llm_model = fields.CharField(max_length=100, null=True)
    llm_temperature = fields.FloatField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "guides"
