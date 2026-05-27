"""
LLM Celery Tasks
- generate_guide_task
- process_chat_message_task
- generate_daily_tip_task
"""

import json
import logging
import os
from datetime import datetime

import redis
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ai_worker.celery_app import celery_app
from ai_worker.prompts.llm_prompts import (
    GUIDE_SYSTEM,
    build_chat_system_prompt,
    build_guide_user_prompt,
)
from ai_worker.rag.chroma_store import search_docs_with_scores, search_text_for_medications
from ai_worker.user_health import load_user_health

logger = logging.getLogger(__name__)

_redis = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)


def _get_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=4096,
        api_key=os.getenv("OPENAI_API_KEY", ""),
    )


def _get_llm_stream():
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=2048,
        streaming=True,
        api_key=os.getenv("OPENAI_API_KEY", ""),
    )


_tortoise_initialized = False


async def _init_tortoise():
    global _tortoise_initialized
    if _tortoise_initialized:
        return
    from tortoise import Tortoise

    db_host = os.getenv("DB_HOST", "mysql")
    db_port = int(os.getenv("DB_PORT", "3306"))
    db_user = os.getenv("DB_USER", "ozcoding")
    db_password = os.getenv("DB_PASSWORD", "pw1234")
    db_name = os.getenv("DB_NAME", "ai_health")
    await Tortoise.init(
        db_url=f"mysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}",
        modules={"models": ["ai_worker.models"]},
    )
    _tortoise_initialized = True


def _run_async(coro):
    import asyncio

    global _tortoise_initialized
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _tortoise_initialized = False
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        raise e
    finally:
        try:
            from tortoise import Tortoise

            loop.run_until_complete(Tortoise.close_connections())
        except Exception:
            pass
        loop.close()
        asyncio.set_event_loop(None)


@celery_app.task(
    bind=True,
    name="ai_worker.task.llm_tasks.generate_guide_task",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def generate_guide_task(self, guide_id: str, record_id: str, user_id: int):
    logger.info(f"[generate_guide] guide_id={guide_id}")
    _run_async(_generate_guide(self, guide_id, record_id, user_id))


async def _generate_guide(task, guide_id: str, record_id: str, user_id: int):
    await _init_tortoise()
    from ai_worker.models import Guide, MedicalRecord, User

    guide = await Guide.get_or_none(id=guide_id)
    if not guide:
        return

    await Guide.filter(id=guide_id).update(status="processing")

    try:
        record = await MedicalRecord.get_or_none(id=record_id)
        if not record or not record.parsed_data:
            raise ValueError(f"OCR result not found: {record_id}")

        medications = record.parsed_data.get("medications", [])
        user = await User.get_or_none(id=user_id)
        user_health = await load_user_health(user_id, user)
        rag_context = search_text_for_medications(medications)

        response = _get_llm().invoke(
            [
                SystemMessage(content=GUIDE_SYSTEM),
                HumanMessage(content=build_guide_user_prompt(medications, user_health, rag_context)),
            ]
        )
        parsed = _parse_json(response.content)
        summary_text = (parsed.get("summary") or "").strip()
        title = summary_text[:15] if summary_text else None

        await Guide.filter(id=guide_id).update(
            status="done",
            title=title,
            medication_guide=parsed.get("medication_guide", ""),
            lifestyle_guide=parsed.get("lifestyle_guide", ""),
            summary=summary_text,
            allergy_warnings=parsed.get("allergy_warnings", []),
            condition_interactions=parsed.get("condition_interactions", []),
        )

        _redis.publish(f"guide:done:{user_id}", json.dumps({"guide_id": guide_id, "status": "done"}))
        logger.info(f"[generate_guide] done guide_id={guide_id}")

    except Exception as exc:
        await Guide.filter(id=guide_id).update(status="failed")
        logger.error(f"[generate_guide] failed: {exc}", exc_info=True)
        raise task.retry(exc=exc) from exc


@celery_app.task(
    bind=True,
    name="ai_worker.task.llm_tasks.process_chat_message_task",
    max_retries=2,
    default_retry_delay=5,
    acks_late=True,
    time_limit=60,
)
def process_chat_message_task(self, session_id: int, message_id: int, user_id: int, user_message: str):
    logger.info(f"[chat] session={session_id} msg={message_id}")
    _run_async(_process_chat(self, session_id, message_id, user_id, user_message))


async def _process_chat(task, session_id: int, message_id: int, user_id: int, user_message: str):
    await _init_tortoise()
    from ai_worker.models import ChatMessage, User

    try:
        user = await User.get_or_none(id=user_id)
        user_health = await load_user_health(user_id, user)

        if _is_off_topic(user_message):
            answer = (
                "MediLog 복약 도우미입니다. 의약품 복용, 건강 관리, 약물 상호작용에 관한 질문만 답변드릴 수 있어요."
            )
            _save_and_publish(session_id, message_id, user_message, answer)
            await ChatMessage.filter(id=message_id).update(content=answer, status="DONE")
            return

        rag_docs, rag_used = search_docs_with_scores(user_message)
        history = _get_history(session_id)

        messages = [SystemMessage(content=build_chat_system_prompt(user_health, rag_docs))]
        for turn in history:
            messages.append(HumanMessage(content=turn["user"]))
            messages.append(SystemMessage(content=turn["assistant"]))
        messages.append(HumanMessage(content=user_message))

        full_response = ""
        for chunk in _get_llm_stream().stream(messages):
            token = chunk.content
            full_response += token
            _redis.publish(
                f"chat:stream:{session_id}",
                json.dumps({"token": token, "message_id": message_id}),
            )

        if not rag_used:
            full_response += "\n\n*참고 문서 없음 — AI 일반 지식 기반 답변입니다.*"

        warning = _drug_interaction_check(user_message, user_health)
        if warning:
            full_response += f"\n\nWarning: {warning}"

        _save_and_publish(session_id, message_id, user_message, full_response)
        await ChatMessage.filter(id=message_id).update(content=full_response, status="DONE")

    except Exception as exc:
        _redis.publish(
            f"chat:stream:{session_id}",
            json.dumps({"error": str(exc), "message_id": message_id, "done": True}),
        )
        logger.error(f"[chat] failed: {exc}", exc_info=True)
        raise task.retry(exc=exc) from exc


@celery_app.task(bind=True, name="ai_worker.task.llm_tasks.generate_daily_tip_task", max_retries=2)
def generate_daily_tip_task(self, tip_id: str, user_id: int):
    logger.info(f"[daily_tip] tip_id={tip_id}")
    try:
        response = _get_llm().invoke(
            [
                SystemMessage(
                    content="Write today health tip in JSON format only: {title, subtitle, body, highlight, category, color_theme}"
                ),
                HumanMessage(content=f"Today is {datetime.now().strftime('%Y-%m-%d')}. Write a health tip."),
            ]
        )
        tip_data = _parse_json(response.content)
        _redis.set(f"daily_tip:{tip_id}", json.dumps(tip_data, ensure_ascii=False), ex=86400)
        logger.info(f"[daily_tip] done tip_id={tip_id}")
    except Exception as exc:
        logger.error(f"[daily_tip] failed: {exc}", exc_info=True)
        raise self.retry(exc=exc) from exc


@celery_app.task(name="ai_worker.task.llm_tasks.generate_daily_tip_scheduled")
def generate_daily_tip_scheduled():
    import uuid

    tip_id = str(uuid.uuid4())
    generate_daily_tip_task.apply_async(kwargs={"tip_id": tip_id, "user_id": 0}, queue="llm")


def _is_off_topic(message: str) -> bool:
    off_topics = [
        "stock",
        "crypto",
        "weather",
        "sports",
        "game",
        "politics",
        "entertainment",
        "주식",
        "코인",
        "투자",
        "날씨",
        "스포츠",
        "게임",
        "정치",
        "연예",
        "영화",
        "쇼핑",
    ]
    return any(kw in message for kw in off_topics)


def _drug_interaction_check(message: str, user_health: dict) -> str | None:
    danger_map = {"아스피린": ["혈우병", "위궤양"], "이부프로펜": ["신부전", "고혈압"]}
    conditions = [c["name"] for c in user_health.get("conditions", [])]
    for drug, dangers in danger_map.items():
        if drug in message:
            for d in dangers:
                if d in conditions:
                    return f"{drug} requires caution for {d} patients."
    return None


def _get_history(session_id: int) -> list[dict]:
    raw = _redis.lrange(f"chat:history:{session_id}", -20, -1)
    history = []
    for i in range(0, len(raw) - 1, 2):
        try:
            history.append(
                {
                    "user": json.loads(raw[i])["content"],
                    "assistant": json.loads(raw[i + 1])["content"],
                }
            )
        except (json.JSONDecodeError, KeyError):
            continue
    return history


def _save_and_publish(session_id: int, message_id: int, user_msg: str, answer: str):
    key = f"chat:history:{session_id}"
    pipe = _redis.pipeline()
    pipe.rpush(key, json.dumps({"role": "user", "content": user_msg}, ensure_ascii=False))
    pipe.rpush(key, json.dumps({"role": "assistant", "content": answer}, ensure_ascii=False))
    pipe.expire(key, 86400)
    pipe.execute()
    _redis.publish(
        f"chat:stream:{session_id}",
        json.dumps({"token": answer, "message_id": message_id, "done": True}, ensure_ascii=False),
    )


def _parse_json(raw: str) -> dict:
    clean = raw.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return {
            "medication_guide": raw,
            "lifestyle_guide": "",
            "summary": "",
            "allergy_warnings": [],
            "condition_interactions": [],
        }
