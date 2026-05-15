# import logging
# import asyncio

# from celery import Task
# from tortoise import Tortoise

# from ai_worker.main import celery_app
# from ai_worker.schemas.ai import AnalysisRequest, AnalysisResult

# logger = logging.getLogger(__name__)

# # ai_worker에서 DB에 접근하기 위한 Tortoise 설정
# TORTOISE_ORM = {
#     "connections": {
#         "default": {
#             "engine": "tortoise.backends.mysql",
#             "dialect": "asyncmy",
#             "credentials": {
#                 "host": "mysql",
#                 "port": 3306,
#                 "user": "ozcoding",
#                 "password": "pw1234",
#                 "database": "ai_health",
#             },
#         },
#     },
#     "apps": {
#         "models": {
#             "models": ["ai_worker.models"],
#         },
#     },
# }


# class AITask(Task):
#     def on_failure(self, exc, task_id, args, kwargs, einfo):
#         logger.error(f"[AI Task] 실패 task_id={task_id}: {exc}")
#         super().on_failure(exc, task_id, args, kwargs, einfo)


# @celery_app.task(
#     base=AITask,
#     bind=True,
#     name="ai_worker.tasks.ai_tasks.analyze_health_data",
#     max_retries=3,
# )
# def analyze_health_data(self, request_data: dict) -> dict:
#     try:
#         request = AnalysisRequest(**request_data)
#         logger.info(f"[AI Task] 분석 시작 user_id={request.user_id} record_id={request.record_id}")

#         result = _run_analysis(request.data)

#         # DB 업데이트 (async → sync 변환)
#         asyncio.run(_update_db(request.record_id, "completed", result))

#         response = AnalysisResult(
#             user_id=request.user_id,
#             record_id=request.record_id,
#             status="completed",
#             result=result,
#             error=None,
#         )
#         logger.info(f"[AI Task] 분석 완료 record_id={request.record_id}")
#         return response.model_dump()

#     except Exception as exc:
#         logger.warning(f"[AI Task] 재시도 {self.request.retries + 1}/3: {exc}")
#         raise self.retry(exc=exc, countdown=30)


# async def _update_db(record_id: int, status: str, result: dict):
#     """분석 완료 후 ai_results 테이블 업데이트"""
#     await Tortoise.init(config=TORTOISE_ORM)
#     try:
#         from tortoise import connections
#         conn = connections.get("default")
#         await conn.execute_query(
#             "UPDATE ai_results SET status=%s, result=%s WHERE health_record_id=%s",
#             [status.upper(), str(result), record_id],
#         )
#     finally:
#         await Tortoise.close_connections()


# def _run_analysis(data: dict) -> dict:
#     # TODO: 실제 AI 모델 코드로 교체
#     return {
#         "summary": "분석 완료 (더미 결과)",
#         "score": 0.85,
#         "recommendations": ["규칙적인 운동", "충분한 수면"],
#     }

import logging
import asyncio
import asyncmy

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

        result = _run_analysis(request.data)

        # DB 업데이트
        asyncio.run(_update_db(request.record_id, result))

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
        raise self.retry(exc=exc, countdown=30)


async def _update_db(record_id: int, result: dict):
    """Tortoise 없이 직접 SQL로 DB 업데이트"""
    import json
    conn = await asyncmy.connect(
        host="mysql",
        port=3306,
        user="ozcoding",
        password="pw1234",
        db="ai_health",
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