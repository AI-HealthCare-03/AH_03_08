from tortoise import fields, models


class CalendarEvent(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="calendar_events")
    medication = fields.ForeignKeyField("models.Medication", related_name="calendar_events")
    event_date = fields.DateField()
    scheduled_time = fields.TimeField()
    status = fields.CharField(max_length=20, default="PENDING")  # PENDING / TAKEN / MISSED
    taken_at = fields.DatetimeField(null=True)
    note = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "calendar_events"