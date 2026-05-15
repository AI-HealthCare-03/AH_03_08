from tortoise import fields, models


class Feedback(models.Model):
    id = fields.UUIDField(primary_key=True)
    guide = fields.ForeignKeyField("models.Guide", related_name="feedbacks")
    user = fields.ForeignKeyField("models.User", related_name="feedbacks")
    rating = fields.IntField()                     # 1~5
    comment = fields.TextField(null=True)
    status = fields.CharField(max_length=20, default="ACTIVE")
    deactive_at = fields.DatetimeField(null=True)
    deactive_by = fields.ForeignKeyField("models.User", related_name="deactivated_feedbacks", null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "feedbacks"