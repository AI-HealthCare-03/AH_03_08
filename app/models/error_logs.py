from tortoise import fields, models


class ErrorLog(models.Model):
    id = fields.UUIDField(primary_key=True)
    access_log = fields.ForeignKeyField("models.AccessLog", related_name="error_logs", null=True)
    status_code = fields.IntField()
    error_type = fields.CharField(max_length=100, null=True)
    message = fields.TextField(null=True)
    stack_trace = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "error_logs"