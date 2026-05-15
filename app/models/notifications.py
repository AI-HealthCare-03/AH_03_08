from tortoise import fields, models


class Notification(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="notifications")
    medication = fields.ForeignKeyField("models.Medication", related_name="notifications")
    title = fields.CharField(max_length=200)
    type = fields.CharField(max_length=50)        # push / sms / email
    scheduled_time = fields.TimeField()
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "notifications"