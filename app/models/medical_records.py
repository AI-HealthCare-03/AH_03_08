from tortoise import fields, models


class MedicalRecord(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="medical_records")
    ocr_raw_text = fields.TextField(null=True)       # OCR 원본 텍스트
    parsed_data = fields.JSONField(null=True)         # 파싱된 데이터
    status = fields.CharField(max_length=20, default="PENDING")  # PENDING / COMPLETED / FAILED
    record_type = fields.IntField(default=0)          # 0: 처방전, 1: 약봉투 등
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "medical_records"