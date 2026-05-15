from tortoise import fields, models


class UnderlyingDisease(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="underlying_diseases")
    underlying_disease_name = fields.CharField(max_length=200)
    severity = fields.CharField(max_length=50, null=True)  # mild / moderate / severe
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "underlying_diseases"