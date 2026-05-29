"""
LLM Celery Tasks
- generate_guide_task
- process_chat_message_task
- generate_daily_tip_task
"""

import asyncio
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


# ─────────────────────────────────────────────────────────────────
# [최적화 10-A] LLM 인스턴스 싱글톤
#
# 문제: _get_llm() / _get_llm_stream() 이 호출마다 ChatOpenAI() 새 인스턴스 생성.
#       HTTP 클라이언트 재초기화, API 키 파싱 등 불필요한 비용 반복.
#
# 해결: 모듈 레벨 변수로 지연 초기화(Lazy singleton).
#       첫 호출 시 1회 생성 후 재사용.
# ─────────────────────────────────────────────────────────────────

_llm: ChatOpenAI | None = None
_llm_stream: ChatOpenAI | None = None


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=4096,
            api_key=os.getenv("OPENAI_API_KEY", ""),
        )
    return _llm


def _get_llm_stream() -> ChatOpenAI:
    global _llm_stream
    if _llm_stream is None:
        _llm_stream = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=2048,
            streaming=True,
            api_key=os.getenv("OPENAI_API_KEY", ""),
        )
    return _llm_stream


# ─────────────────────────────────────────────────────────────────
# [최적화 7] Tortoise 초기화 헬퍼
#
# 문제: 기존 _run_async()는 호출마다 new_event_loop() 생성 후
#       전역 _tortoise_initialized 플래그를 False로 리셋 → 매 태스크마다
#       Tortoise.init() 재실행 (DB 연결 풀 생성·해제 반복).
#
# 해결: asyncio.run()으로 단순화. Tortoise init/close를 각 async 함수
#       내부에서 명시적으로 처리하여 코드 흐름을 명확하게 유지.
# ─────────────────────────────────────────────────────────────────


def _db_url() -> str:
    db_host = os.getenv("DB_HOST", "mysql")
    db_port = os.getenv("DB_PORT", "3306")
    db_user = os.getenv("DB_USER", "ozcoding")
    db_password = os.getenv("DB_PASSWORD", "pw1234")
    db_name = os.getenv("DB_NAME", "ai_health")
    return f"mysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


@celery_app.task(
    bind=True,
    name="ai_worker.tasks.llm_task.generate_guide_task",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def generate_guide_task(self, guide_id: str, record_id: str, user_id: int):
    logger.info(f"[generate_guide] guide_id={guide_id}")
    asyncio.run(_generate_guide(self, guide_id, record_id, user_id))


async def _generate_guide(task, guide_id: str, record_id: str, user_id: int):
    # [12] Tortoise 직접 접근 제거 — callback.py 통해 FastAPI에 위임
    await _do_generate_guide(task, guide_id, record_id, user_id)


async def _do_generate_guide(task, guide_id: str, record_id: str, user_id: int):
    from tortoise import Tortoise

    from ai_worker.callback import guide_done, guide_failed
    from ai_worker.models import MedicalRecord, User

    # MedicalRecord / User 조회는 여전히 직접 접근 (읽기 전용)
    await Tortoise.init(db_url=_db_url(), modules={"models": ["ai_worker.models"]})
    try:
        record = await MedicalRecord.get_or_none(id=record_id)
        if not record or not record.parsed_data:
            guide_failed(guide_id, user_id)
            raise ValueError(f"OCR result not found: {record_id}")

        medications = record.parsed_data.get("medications", [])
        user = await User.get_or_none(id=user_id)
        user_health = await load_user_health(user_id, user)
    finally:
        await Tortoise.close_connections()

    rag_context = search_text_for_medications(medications)

    try:
        response = _get_llm().invoke(
            [
                SystemMessage(content=GUIDE_SYSTEM),
                HumanMessage(content=build_guide_user_prompt(medications, user_health, rag_context)),
            ]
        )
        parsed = _parse_json(response.content)
        summary_text = (parsed.get("summary") or "").strip()

        # [최적화 10-B] 파싱 실패 시 가이드를 failed 상태로 저장
        if parsed is None:
            raise ValueError("LLM 응답을 JSON으로 파싱할 수 없습니다.")

        summary_text = (parsed.get("summary") or "").strip()

        # [12] DB 저장 책임을 FastAPI에 위임 (callback HTTP 호출)
        ok = guide_done(
            guide_id=guide_id,
            user_id=user_id,
            medication_guide=parsed.get("medication_guide", ""),
            lifestyle_guide=parsed.get("lifestyle_guide", ""),
            summary_text=summary_text,
            allergy_warnings=parsed.get("allergy_warnings", []),
            condition_interactions=parsed.get("condition_interactions", []),
        )
        if not ok:
            raise RuntimeError("guide_done callback 실패")

        logger.info(f"[generate_guide] done guide_id={guide_id}")

    except Exception as exc:
        guide_failed(guide_id, user_id)
        logger.error(f"[generate_guide] failed: {exc}", exc_info=True)
        raise task.retry(exc=exc) from exc


@celery_app.task(
    bind=True,
    name="ai_worker.tasks.llm_task.process_chat_message_task",
    max_retries=2,
    default_retry_delay=5,
    acks_late=True,
    time_limit=60,
)
def process_chat_message_task(self, session_id: int, message_id: int, user_id: int, user_message: str):
    logger.info(f"[chat] session={session_id} msg={message_id}")
    asyncio.run(_process_chat(self, session_id, message_id, user_id, user_message))


async def _process_chat(task, session_id: int, message_id: int, user_id: int, user_message: str):
    from tortoise import Tortoise

    await Tortoise.init(db_url=_db_url(), modules={"models": ["ai_worker.models"]})
    try:
        await _do_process_chat(task, session_id, message_id, user_id, user_message)
    finally:
        await Tortoise.close_connections()


async def _do_process_chat(task, session_id: int, message_id: int, user_id: int, user_message: str):
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


@celery_app.task(bind=True, name="ai_worker.tasks.llm_task.generate_daily_tip_task", max_retries=2)
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
        if tip_data is None:
            raise ValueError("daily_tip LLM 응답 JSON 파싱 실패")
        _redis.set(f"daily_tip:{tip_id}", json.dumps(tip_data, ensure_ascii=False), ex=86400)
        logger.info(f"[daily_tip] done tip_id={tip_id}")
    except Exception as exc:
        logger.error(f"[daily_tip] failed: {exc}", exc_info=True)
        raise self.retry(exc=exc) from exc


@celery_app.task(name="ai_worker.tasks.llm_task.generate_daily_tip_scheduled")
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


def _parse_json(raw: str) -> dict | None:
    """
    LLM 응답 문자열을 JSON dict로 파싱한다.

    [최적화 10-B] 파싱 실패 처리 개선
    문제: 기존에는 실패 시 raw text를 medication_guide에 통째로 넣어 반환
          → 클라이언트가 구조화되지 않은 텍스트를 받아 파싱 오류 발생.
    해결: 실패 시 None 반환 → 호출부에서 Guide.status="failed" 처리.
    """
    # 마크다운 코드 펜스 제거 (```json ... ``` 또는 ``` ... ```)
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.removeprefix("```json").removeprefix("```")
        clean = clean.removesuffix("```").strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        logger.error(f"[_parse_json] JSON 파싱 실패. 응답 앞 200자: {clean[:200]!r}")
        return None
