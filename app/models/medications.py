from tortoise import fields, models


class Medication(models.Model):
    id = fields.UUIDField(primary_key=True)
    medical_record = fields.ForeignKeyField("models.MedicalRecord", related_name="medications")
    drug_name = fields.CharField(max_length=200)      # 약품명
    dosage = fields.CharField(max_length=100, null=True)      # 용량 (예: 500mg)
    frequency = fields.CharField(max_length=100, null=True)   # 복용 횟수 (예: 하루 3회)
    instructions = fields.TextField(null=True)        # 복용 지시사항
    warnings = fields.TextField(null=True)            # 주의사항
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "medications"