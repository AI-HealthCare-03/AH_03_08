import logging

from celery import Task

from ai_worker.celery_app import celery_app
from ai_worker.core.config import config
from ai_worker.schemas.ai import AnalysisRequest, AnalysisResult

logger = logging.getLogger(__name__)


class AITask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"[AI Task] 실패 task_id={task_id}: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(
    base=AITask,
    bind=True,
    name="ai_worker.task.ai_tasks.analyze_health_data",
    max_retries=3,
)
def analyze_health_data(self, request_data: dict) -> dict:
    try:
        request = AnalysisRequest(**request_data)
        logger.info(f"[AI Task] 분석 시작 user_id={request.user_id} record_id={request.record_id}")

        result = _run_analysis(request.data)

        response = AnalysisResult(
            user_id=request.user_id,
            record_id=request.record_id,
            status="completed",
            result=result,
            error=None,
        )
        logger.info(f"[AI Task] 분석 완료 record_id={request.record_id}")
        return response.model_dump()

    except Exception as exc:
        logger.warning(f"[AI Task] 재시도 {self.request.retries + 1}/3: {exc}")
        raise self.retry(exc=exc, countdown=30) from exc


async def _update_db(record_id: int, result: dict):
    """[수정 4] 하드코딩된 DB 자격증명 → config 환경변수로 교체"""
    import json

    import asyncmy

    # 기존: host="mysql", user="ozcoding", password="pw1234" 하드코딩
    # 수정: config 객체에서 주입
    conn = await asyncmy.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        db=config.DB_NAME,
    )
    try:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE ai_results SET status='COMPLETED', result=%s WHERE health_record_id=%s",
                (json.dumps(result, ensure_ascii=False), record_id),
            )
        await conn.commit()
        logger.info(f"[AI Task] DB 업데이트 완료 record_id={record_id}")
    finally:
        conn.close()


def _run_analysis(data: dict) -> dict:
    # TODO: 실제 AI 모델 코드로 교체
    return {
        "summary": "분석 완료 (더미 결과)",
        "score": 0.85,
        "recommendations": ["규칙적인 운동", "충분한 수면"],
    }
