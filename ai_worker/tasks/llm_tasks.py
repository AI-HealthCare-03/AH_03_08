"""
LLM Celery Tasks
- generate_guide_task
- process_chat_message_task
- generate_daily_tip_task
"""

import json
import logging
import os
from datetime import date, datetime

import redis
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ai_worker.celery_app import celery_app
from ai_worker.prompts.llm_prompts import (
    GUIDE_SYSTEM,
    build_chat_system_prompt,
    build_guide_user_prompt,
)

logger = logging.getLogger(__name__)

_redis = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)

GUIDE_LLM_MODEL = "gpt-4o-mini"
GUIDE_LLM_TEMPERATURE = 0.3


def _medications_for_prompt(parsed_data: dict | list | None) -> list[dict]:
    """parsed_data(JSON)에서 약 목록을 꺼내 build_guide_user_prompt / RAG용 형식으로 맞춘다."""
    if not parsed_data:
        return []
    if isinstance(parsed_data, list):
        raw_list = parsed_data
    else:
        raw_list = parsed_data.get("medications") or []
    if not isinstance(raw_list, list):
        return []

    out: list[dict] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        name = item.get("drug_name") or item.get("name")
        dosage = item.get("dosage")
        freq = item.get("frequency")
        duration = item.get("duration")
        if duration is None and item.get("days") is not None:
            duration = f"{item['days']}일분"

        out.append(
            {
                "drug_name": name or "알 수 없음",
                "dosage": "-" if dosage is None else str(dosage),
                "frequency": "-" if freq is None else str(freq),
                "duration": "-" if duration is None else str(duration),
                "instructions": item.get("instructions") or "-",
            }
        )
    return out


def _get_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=4096,
        api_key=os.getenv("OPENAI_API_KEY", ""),
    )


def _get_guide_llm():
    return ChatOpenAI(
        model=GUIDE_LLM_MODEL,
        temperature=GUIDE_LLM_TEMPERATURE,
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


_embeddings = None
_vectorstore = None


def _get_vectorstore():
    global _embeddings, _vectorstore
    if _vectorstore is None:
        try:
            from langchain_chroma import Chroma
            from langchain_community.embeddings import HuggingFaceEmbeddings

            _embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            _vectorstore = Chroma(
                collection_name="medical_knowledge",
                embedding_function=_embeddings,
                persist_directory=os.getenv("CHROMA_PERSIST_DIR", "/data/chromadb"),
            )
        except Exception as e:
            logger.warning(f"ChromaDB init failed: {e}")
    return _vectorstore


_tortoise_initialized = False

GUIDE_TORTOISE_MODELS = [
    "app.models.users",
    "app.models.medical_records",
    "app.models.guides",
    "app.models.feedbacks",
    "app.models.allergies",
    "app.models.underlying_diseases",
]

CHAT_TORTOISE_MODELS = ["ai_worker.models"]


async def _init_tortoise(model_modules: list[str] | None = None):
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
        modules={"models": model_modules or GUIDE_TORTOISE_MODELS},
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
    name="ai_worker.tasks.llm_tasks.generate_guide_task",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def generate_guide_task(self, guide_id: str, record_id: str, user_id: int):
    logger.info(f"[generate_guide] guide_id={guide_id}")
    _run_async(_generate_guide(self, guide_id, record_id, user_id))


async def _generate_guide(task, guide_id: str, record_id: str, user_id: int):
    await _init_tortoise(GUIDE_TORTOISE_MODELS)
    from app.models.guides import Guide
    from app.models.medical_records import MedicalRecord
    from app.models.users import User

    medical_record_id = record_id

    guide = await Guide.get_or_none(id=guide_id, user_id=user_id)
    if not guide:
        logger.warning(f"[generate_guide] guide not found: {guide_id}")
        return

    await Guide.filter(id=guide_id).update(status="processing")

    try:
        record = await MedicalRecord.get_or_none(id=medical_record_id, user_id=user_id)
        if not record or not record.parsed_data:
            raise ValueError(f"OCR result not found: {medical_record_id}")
        if record.status not in ("COMPLETED", "DONE", "done"):
            raise ValueError(f"Medical record not ready: {medical_record_id} (status={record.status})")

        medications = _medications_for_prompt(record.parsed_data)

        from app.models.allergies import Allergy
        from app.models.underlying_diseases import UnderlyingDisease

        user = await User.get_or_none(id=user_id)
        if not user:
            user_health = {
                "age": None,
                "gender": None,
                "height_cm": None,
                "weight_kg": None,
                "allergies": [],
                "conditions": [],
            }
        else:
            age = None
            if user.birthday:
                today = date.today()
                age = (
                    today.year
                    - user.birthday.year
                    - ((today.month, today.day) < (user.birthday.month, user.birthday.day))
                )
            gender = user.gender
            if hasattr(gender, "value"):
                gender = gender.value

            allergy_rows = await Allergy.filter(user_id=user_id).all()
            disease_rows = await UnderlyingDisease.filter(user_id=user_id).all()

            user_health = {
                "age": age,
                "gender": gender,
                "height_cm": user.height_cm,
                "weight_kg": user.weight_kg,
                "allergies": [
                    {"name": row.allergy_name, "severity": row.severity or "unknown"} for row in allergy_rows
                ],
                "conditions": [{"name": row.underlying_disease_name} for row in disease_rows],
            }

        rag_context = _rag_search_text(medications)

        from app.services.feedback_prompt_insights import build_feedback_addon_for_llm

        feedback_addon = await build_feedback_addon_for_llm(str(guide.id), guide.prompt_version)

        response = _get_guide_llm().invoke(
            [
                SystemMessage(content=GUIDE_SYSTEM),
                HumanMessage(content=build_guide_user_prompt(medications, user_health, rag_context, feedback_addon)),
            ]
        )
        parsed = _parse_json(response.content)

        await Guide.filter(id=guide_id).update(
            status="done",
            medication_guide=parsed.get("medication_guide", ""),
            lifestyle_guide=parsed.get("lifestyle_guide", ""),
            summary_text=parsed.get("summary", ""),
            allergy_warnings=parsed.get("allergy_warnings", []),
            condition_interactions=parsed.get("condition_interactions", []),
            llm_model=GUIDE_LLM_MODEL,
            llm_temperature=GUIDE_LLM_TEMPERATURE,
        )

        _redis.publish(
            f"guide:done:{user_id}",
            json.dumps({"guide_id": guide_id, "status": "done"}, ensure_ascii=False),
        )
        logger.info(f"[generate_guide] done guide_id={guide_id}")

    except Exception as exc:
        await Guide.filter(id=guide_id).update(status="failed")
        logger.error(f"[generate_guide] failed: {exc}", exc_info=True)
        raise task.retry(exc=exc) from exc


@celery_app.task(
    bind=True,
    name="ai_worker.tasks.llm_tasks.process_chat_message_task",
    max_retries=2,
    default_retry_delay=5,
    acks_late=True,
    time_limit=60,
)
def process_chat_message_task(self, session_id: int, message_id: int, user_id: int, user_message: str):
    logger.info(f"[chat] session={session_id} msg={message_id}")
    _run_async(_process_chat(self, session_id, message_id, user_id, user_message))


async def _process_chat(task, session_id: int, message_id: int, user_id: int, user_message: str):
    await _init_tortoise(CHAT_TORTOISE_MODELS)
    from ai_worker.models import ChatMessage, User

    try:
        user = await User.get_or_none(id=user_id)
        user_health = _build_user_health_sync(user)

        if _is_off_topic(user_message):
            answer = (
                "MediLog 복약 도우미입니다. 의약품 복용, 건강 관리, 약물 상호작용에 관한 질문만 답변드릴 수 있어요."
            )
            _save_and_publish(session_id, message_id, user_message, answer)
            await ChatMessage.filter(id=message_id).update(content=answer, status="DONE")
            return

        rag_docs, rag_used = _rag_search_docs(user_message)
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
            full_response += "\n\n*No reference documents - based on LLM knowledge*"

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


@celery_app.task(bind=True, name="ai_worker.tasks.llm_tasks.generate_daily_tip_task", max_retries=2)
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


@celery_app.task(name="ai_worker.tasks.llm_tasks.generate_daily_tip_scheduled")
def generate_daily_tip_scheduled():
    import uuid

    tip_id = str(uuid.uuid4())
    generate_daily_tip_task.apply_async(kwargs={"tip_id": tip_id, "user_id": 0}, queue="llm")


def _build_user_health_sync(user) -> dict:
    if not user:
        return {}
    age = None
    if user.birthday:
        today = date.today()
        age = today.year - user.birthday.year - ((today.month, today.day) < (user.birthday.month, user.birthday.day))

    gender = user.gender
    if hasattr(gender, "value"):
        gender = gender.value

    return {
        "age": age,
        "gender": gender,
        "height_cm": user.height_cm,
        "weight_kg": user.weight_kg,
        "allergies": [],
        "conditions": [],
    }


def _rag_search_text(medications: list) -> str:
    if not medications:
        return ""
    try:
        vs = _get_vectorstore()
        if not vs:
            return ""
        query = " ".join(m.get("drug_name", "") for m in medications)
        docs = vs.similarity_search(query, k=5)
        return "\n\n".join(f"[{i + 1}] {d.page_content}" for i, d in enumerate(docs))
    except Exception as e:
        logger.warning(f"RAG search failed: {e}")
        return ""


def _rag_search_docs(query: str) -> tuple:
    try:
        vs = _get_vectorstore()
        if not vs:
            return [], False
        results = vs.similarity_search_with_relevance_scores(query, k=3)
        filtered = [doc for doc, score in results if score >= 0.6]
        return filtered, bool(filtered)
    except Exception as e:
        logger.warning(f"RAG search failed: {e}")
        return [], False


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


# llm_task.py 통합 — 하위 호환용 별칭
generate_guide = generate_guide_task


@celery_app.task(name="ai_worker.tasks.llm_task.generate_guide")
def generate_guide_legacy(
    guide_id: str,
    record_id: str | None = None,
    user_id: int | None = None,
    **kwargs,
):
    """Deprecated task name; delegates to generate_guide_task."""
    if record_id is None:
        medical_record_data = kwargs.get("medical_record_data") or {}
        record_id = medical_record_data.get("medical_record_id")
    if user_id is None:
        user_info = kwargs.get("user_info") or {}
        user_id = user_info.get("user_id")
    if not record_id or user_id is None:
        raise ValueError("record_id and user_id are required")
    return generate_guide_task.apply_async(
        kwargs={"guide_id": guide_id, "record_id": str(record_id), "user_id": int(user_id)},
        queue="llm",
    )
