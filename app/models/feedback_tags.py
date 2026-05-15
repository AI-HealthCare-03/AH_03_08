from tortoise import fields, models


class FeedbackTag(models.Model):
    id = fields.UUIDField(primary_key=True)
    type = fields.CharField(max_length=50)
    label = fields.CharField(max_length=100)
    display_order = fields.IntField(default=0)

    class Meta:
        table = "feedback_tags"


class FeedbackTagSelection(models.Model):
    id = fields.UUIDField(primary_key=True)
    feedback = fields.ForeignKeyField("models.Feedback", related_name="tag_selections")
    tag = fields.ForeignKeyField("models.FeedbackTag", related_name="selections")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "feedback_tag_selections"