from tortoise import fields, models


class ModelMetric(models.Model):
    id = fields.UUIDField(primary_key=True)
    model_type = fields.CharField(max_length=100)
    latency_ms = fields.FloatField(null=True)
    token_input = fields.IntField(null=True)
    token_output = fields.IntField(null=True)
    confidence_score = fields.FloatField(null=True)
    success = fields.BooleanField(default=True)
    reference = fields.ForeignKeyField("models.Guide", related_name="model_metrics", null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "model_metrics"


class MetricSnapshot(models.Model):
    id = fields.UUIDField(primary_key=True)
    model_type = fields.CharField(max_length=100)
    snapshot_date = fields.DateField()
    avg_latency_ms = fields.FloatField(null=True)
    success_rate = fields.FloatField(null=True)
    avg_rating = fields.FloatField(null=True)
    total_count = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "metric_snapshots"