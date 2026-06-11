import asyncio
import logging
import os
from datetime import UTC

from ai_worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def _db_url() -> str:
    return (
        f"mysql://{os.getenv('DB_USER', 'ozcoding')}:"
        f"{os.getenv('DB_PASSWORD', 'pw1234')}@"
        f"{os.getenv('DB_HOST', 'mysql')}:"
        f"{os.getenv('DB_PORT', '3306')}/"
        f"{os.getenv('DB_NAME', 'ai_health')}"
    )


@celery_app.task(name="ai_worker.tasks.metric_task.aggregate_metric_snapshots")
def aggregate_metric_snapshots():
    asyncio.run(_do_aggregate_metric_snapshots())


async def _do_aggregate_metric_snapshots():
    from datetime import datetime, timedelta

    from tortoise import Tortoise

    await Tortoise.init(
        db_url=_db_url(),
        modules={"models": ["ai_worker.models"]},
    )
    try:
        from app.models.model_metrics import ModelMetric, MetricSnapshot

        today = datetime.now(UTC).date()
        yesterday = today - timedelta(days=1)
        metrics = await ModelMetric.filter(
            created_at__gte=datetime(yesterday.year, yesterday.month, yesterday.day, tzinfo=UTC),
            created_at__lt=datetime(today.year, today.month, today.day, tzinfo=UTC),
        )
        if not metrics:
            return
        model_types = set(m.model_type for m in metrics)
        for model_type in model_types:
            type_metrics = [m for m in metrics if m.model_type == model_type]
            success_list = [m for m in type_metrics if m.success]
            latencies = [m.latency_ms for m in success_list if m.latency_ms]
            avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else None
            success_rate = round(len(success_list) / len(type_metrics), 4) if type_metrics else None
            snapshot, created = await MetricSnapshot.get_or_create(
                model_type=model_type,
                snapshot_date=yesterday,
                defaults={
                    "avg_latency_ms": avg_latency,
                    "success_rate": success_rate,
                    "total_count": len(type_metrics),
                },
            )
            if not created:
                snapshot.avg_latency_ms = avg_latency
                snapshot.success_rate = success_rate
                snapshot.total_count = len(type_metrics)
                await snapshot.save(update_fields=["avg_latency_ms", "success_rate", "total_count"])
        logger.info(f"[metric_snapshot] done: {yesterday} / {len(model_types)} models")
    finally:
        await Tortoise.close_connections()