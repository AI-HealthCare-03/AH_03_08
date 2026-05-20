import logging

from celery import Task

from ai_worker.main import celery_app
from ai_worker.schemas.ai import AnalysisRequest, AnalysisResult

logger = logging.getLogger(__name__)


class AITask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"[AI Task] 실패 task_id={task_id}: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(
    base=AITask,
    bind=True,
    name="ai_worker.tasks.ai_tasks.analyze_health_data",
    max_retries=3,
)
def analyze_health_data(self, request_data: dict) -> dict:
    try:
        request = AnalysisRequest(**request_data)
        logger.info(f"[AI Task] 분석 시작 user_id={request.user_id} record_id={request.record_id}")

        # TODO: LLM 기반 복약/생활습관 가이드 생성 구현 (REQ-GUIDE-001)
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
        raise self.retry(exc=exc, countdown=30 * (2**self.request.retries)) from exc


def _run_analysis(data: dict) -> dict:
    # TODO: LLM 기반 복약/생활습관 가이드 생성 구현 (REQ-GUIDE-001)
    raise NotImplementedError
