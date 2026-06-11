from tortoise import fields, models


class User(models.Model):
    id = fields.BigIntField(primary_key=True)
    gender = fields.CharField(max_length=6)
    birth_date = fields.DateField()
    height_cm = fields.FloatField(null=True)
    weight_kg = fields.FloatField(null=True)

    class Meta:
        table = "users"


class MedicalRecord(models.Model):
    id = fields.CharField(max_length=36, primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="records")
    ocr_raw_text = fields.TextField(null=True)  # OCR 추출 원문
    parsed_data = fields.JSONField(null=True)
    status = fields.CharField(max_length=20, default="PENDING")

    class Meta:
        table = "medical_records"


class Guide(models.Model):
    id = fields.CharField(max_length=36, primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="guides")
    record = fields.ForeignKeyField("models.MedicalRecord", related_name="guides", source_field="record_id")
    status = fields.CharField(max_length=20, default="processing")
    title = fields.CharField(max_length=200, null=True)
    medication_guide = fields.TextField(null=True)
    lifestyle_guide = fields.TextField(null=True)
    summary_text = fields.TextField(null=True)  # app/models/guides.py 와 속성명 통일
    allergy_warnings = fields.JSONField(null=True)
    condition_interactions = fields.JSONField(null=True)

    class Meta:
        table = "guides"


class ChatSession(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="chat_sessions")
    guide = fields.ForeignKeyField("models.Guide", null=True, related_name="chat_sessions")

    class Meta:
        table = "chat_sessions"


class ChatMessage(models.Model):
    id = fields.UUIDField(primary_key=True)
    session = fields.ForeignKeyField("models.ChatSession", related_name="messages")
    role = fields.CharField(max_length=10)
    content = fields.TextField(default="")
    status = fields.CharField(max_length=20, default="DONE")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chat_messages"


class Allergy(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="allergies")
    allergy_name = fields.CharField(max_length=200)
    severity = fields.CharField(max_length=50, null=True)

    class Meta:
        table = "allergies"


class UnderlyingDisease(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="underlying_diseases")
    underlying_disease_name = fields.CharField(max_length=200)
    severity = fields.CharField(max_length=50, null=True)

    class Meta:
        table = "underlying_diseases"


class Medication(models.Model):
    id = fields.UUIDField(primary_key=True)
    medical_record = fields.ForeignKeyField("models.MedicalRecord", related_name="medications")
    drug_name = fields.CharField(max_length=200)
    dosage = fields.CharField(max_length=100, null=True)
    frequency = fields.CharField(max_length=100, null=True)
    instructions = fields.TextField(null=True)
    warnings = fields.TextField(null=True)
    drug_class = fields.CharField(max_length=200, null=True)
    start_date = fields.DateField(null=True)
    end_date = fields.DateField(null=True)
    interval = fields.IntField(null=True)
    memo = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "medications"


class Notification(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="notifications")
    medication = fields.ForeignKeyField("models.Medication", related_name="notifications")
    title = fields.CharField(max_length=200)
    type = fields.CharField(max_length=50)
    scheduled_time = fields.TimeField()
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "notifications"
