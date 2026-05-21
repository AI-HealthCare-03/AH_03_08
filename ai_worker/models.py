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
    parsed_data = fields.JSONField(null=True)
    status = fields.CharField(max_length=20, default="PENDING")

    class Meta:
        table = "medical_records"


class Guide(models.Model):
    id = fields.CharField(max_length=36, primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="guides")
    record = fields.ForeignKeyField("models.MedicalRecord", related_name="guides", source_field="record_id")
    status = fields.CharField(max_length=20, default="processing")
    medication_guide = fields.TextField(null=True)
    lifestyle_guide = fields.TextField(null=True)
    summary = fields.TextField(null=True, source_field="summary_text")
    allergy_warnings = fields.JSONField(null=True)
    condition_interactions = fields.JSONField(null=True)

    class Meta:
        table = "guides"


class ChatSession(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="chat_sessions")

    class Meta:
        table = "chat_sessions"


class ChatMessage(models.Model):
    id = fields.BigIntField(primary_key=True)
    session = fields.ForeignKeyField("models.ChatSession", related_name="messages")
    role = fields.CharField(max_length=10)
    content = fields.TextField(default="")
    status = fields.CharField(max_length=20, default="DONE")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chat_messages"
