from tortoise import fields, models


class Guide(models.Model):
    """
    복약 가이드 정규 모델 (app/models/guides.py 단일 정의).
    - app/models/llm.py 의 Guide 클래스는 제거됨.
    - summary_text: DB 컬럼명. 코드에서는 guide.summary_text 로 접근.
    - on_delete=CASCADE: 유저/레코드 삭제 시 연쇄 삭제.
    """

    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="guides", on_delete=fields.CASCADE
    )
    record = fields.ForeignKeyField(
        "models.MedicalRecord",
        related_name="guides",
        source_field="record_id",
        on_delete=fields.CASCADE,
    )
    status = fields.CharField(max_length=20, default="processing")  # processing / done / failed
    medication_guide = fields.TextField(null=True)
    lifestyle_guide = fields.TextField(null=True)
    summary_text = fields.TextField(null=True)          # DB 컬럼명 summary_text
    allergy_warnings = fields.JSONField(default=list)
    condition_interactions = fields.JSONField(default=list)
    prompt_version = fields.CharField(max_length=20, default="v1.0")
    llm_model = fields.CharField(max_length=100, null=True)
    llm_temperature = fields.FloatField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "guides"