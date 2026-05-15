from tortoise import fields, models


class ChatSession(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="chat_sessions")
    guide = fields.ForeignKeyField("models.Guide", related_name="chat_sessions", null=True)
    title = fields.CharField(max_length=200, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    last_active_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "chat_sessions"