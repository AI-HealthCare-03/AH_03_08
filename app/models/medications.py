from tortoise import fields, models


class Medication(models.Model):
    id = fields.UUIDField(primary_key=True)
    medical_record = fields.ForeignKeyField("models.MedicalRecord", related_name="medications")
    drug_name = fields.CharField(max_length=200)
    dosage = fields.CharField(max_length=100, null=True)
    frequency = fields.CharField(max_length=100, null=True)
    instructions = fields.TextField(null=True)
    warnings = fields.TextField(null=True)
    start_date = fields.DateField(null=True)
    end_date = fields.DateField(null=True)
    interval_days = fields.IntField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "medications"