from tortoise import fields, models


class GuideAsset(models.Model):
    id = fields.UUIDField(primary_key=True)
    guide = fields.ForeignKeyField("models.Guide", related_name="assets")
    asset_type = fields.CharField(max_length=50)
    file_url = fields.CharField(max_length=500)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "guide_assets"