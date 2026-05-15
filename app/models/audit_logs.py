from tortoise import fields, models


class AuditLog(models.Model):
    id = fields.UUIDField(primary_key=True)
    actor = fields.ForeignKeyField("models.User", related_name="audit_logs", null=True)
    action = fields.CharField(max_length=100)
    target_type = fields.CharField(max_length=100)
    target_id = fields.UUIDField(null=True)
    before_value = fields.JSONField(null=True)
    after_value = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "audit_logs"