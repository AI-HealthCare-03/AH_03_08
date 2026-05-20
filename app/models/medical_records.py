from tortoise import fields, models


class MedicalRecord(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="medical_records")
    record_type = fields.CharField(max_length=20)
    status = fields.CharField(max_length=20, default="PENDING")
    parsed_data = fields.JSONField(null=True)
    file_url = fields.CharField(max_length=500, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "medical_records"
