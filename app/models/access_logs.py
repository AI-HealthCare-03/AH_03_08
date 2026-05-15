from tortoise import fields, models


class AccessLog(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="access_logs", null=True)
    method = fields.CharField(max_length=10)       # GET / POST / PATCH 등
    endpoint = fields.CharField(max_length=500)
    status_code = fields.IntField()
    latency_ms = fields.IntField(null=True)
    request_body = fields.TextField(null=True)
    response_body = fields.TextField(null=True)
    ip_address = fields.CharField(max_length=50, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "access_logs"