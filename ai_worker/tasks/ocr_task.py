import asyncio
import logging

import asyncmy
from celery import Task

from ai_worker.core.config import Config
from ai_worker.main import celery_app
from ai_worker.schemas.record_schemas import OcrTaskResult

logger = logging.getLogger(__name__)
_config = Config()


class OcrTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"[OCR Task] 최종 실패 task_id={task_id}: {exc}")
        record_id = args[0] if args else None
        if record_id:
            asyncio.run(_update_status(record_id, "FAILED"))
        super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(
    base=OcrTask,
    bind=True,
    name="ai_worker.tasks.ocr_task.process_ocr",
    max_retries=3,
)
def process_ocr(self, record_id: str, file_path: str) -> dict:
    try:
        result = asyncio.run(_run_ocr(file_path))
        asyncio.run(_update_db(record_id, result["raw_text"]))
        logger.info(f"[OCR Task] 완료 record_id={record_id}")
        return OcrTaskResult(record_id=record_id, parsed_data=result).model_dump()
    except Exception as exc:
        logger.warning(f"[OCR Task] 재시도 {self.request.retries + 1}/3: {exc}")
        raise self.retry(exc=exc, countdown=30) from exc


async def _run_ocr(file_path: str) -> dict:
    # TODO: CLOVA OCR API 연동으로 교체
    logger.info(f"Running OCR on {file_path}")
    return {"raw_text": "", "fields": {}}


async def _get_conn() -> asyncmy.Connection:
    return await asyncmy.connect(
        host=_config.DB_HOST,
        port=_config.DB_PORT,
        user=_config.DB_USER,
        password=_config.DB_PASSWORD,
        db=_config.DB_NAME,
    )


async def _update_db(record_id: str, ocr_raw_text: str) -> None:
    conn = await _get_conn()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE medical_records SET ocr_raw_text=%s, status='COMPLETED' WHERE id=%s",
                (ocr_raw_text, record_id),
            )
        await conn.commit()
        logger.info(f"[OCR Task] DB 업데이트 완료 record_id={record_id}")
    finally:
        conn.close()


async def _update_status(record_id: str, status: str) -> None:
    conn = await _get_conn()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE medical_records SET status=%s WHERE id=%s",
                (status, record_id),
            )
        await conn.commit()
        logger.info(f"[OCR Task] 상태 업데이트 record_id={record_id} status={status}")
    finally:
        conn.close()
