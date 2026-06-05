"""
개선된 LLM Celery Tasks

변경 사항:
1. generate_guide_task: 약물 상호작용 분석 2-pass 처리 추가
2. generate_daily_tip_task: 개인화 + 한국어 + 계절 컨텍스트
3. process_chat_message_task: 오프토픽 LLM 판단 방식 개선
4. 신규: check_drug_interactions_task (약물 상호작용 전용 태스크)
5. 재시도 지수 백오프(exponential backoff) 적용
6. 응답 검증 강화 (필수 키 존재 여부 체크)
"""

import asyncio
import json
import logging
import os
from datetime import UTC, datetime

import redis
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ai_worker.celery_app import celery_app
from ai_worker.prompts.llm_prompts import (
    GUIDE_SYSTEM,
    INTERACTION_CHECK_SYSTEM,
    build_chat_system_prompt,
    build_daily_tip_prompt,
    build_guide_user_prompt,
    build_interaction_check_prompt,
)
from ai_worker.rag.chroma_store import search_docs_with_scores, search_text_for_medications
from ai_worker.user_health import load_user_health

logger = logging.getLogger(__name__)

_redis = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)

# ─────────────────────────────────────────────────────────────────
# LLM 싱글톤
# ─────────────────────────────────────────────────────────────────

_llm: ChatOpenAI | None = None
_llm_stream: ChatOpenAI | None = None


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.1,  # 개선: 0 → 0.1 (약간의 다양성, 더 자연스러운 문장)
            max_tokens=4096,
            api_key=os.getenv("OPENAI_API_KEY", ""),
        )
    return _llm


def _get_llm_stream() -> ChatOpenAI:
    global _llm_stream
    if _llm_stream is None:
        _llm_stream = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.1,
            max_tokens=2048,
            streaming=True,
            api_key=os.getenv("OPENAI_API_KEY", ""),
        )
    return _llm_stream


def _db_url() -> str:
    return (
        f"mysql://{os.getenv('DB_USER', 'ozcoding')}:"
        f"{os.getenv('DB_PASSWORD', 'pw1234')}@"
        f"{os.getenv('DB_HOST', 'mysql')}:"
        f"{os.getenv('DB_PORT', '3306')}/"
        f"{os.getenv('DB_NAME', 'ai_health')}"
    )


# ─────────────────────────────────────────────────────────────────
# 복약 가이드 생성 태스크 (개선)
# ─────────────────────────────────────────────────────────────────


@celery_app.task(
    bind=True,
    name="ai_worker.tasks.llm_task.generate_guide_task",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def generate_guide_task(self, guide_id: str, record_id: str, user_id: int):
    logger.info(f"[generate_guide] guide_id={guide_id}")
    asyncio.run(_do_generate_guide(self, guide_id, record_id, user_id))


async def _do_generate_guide(task, guide_id: str, record_id: str, user_id: int):
    from tortoise import Tortoise

    from ai_worker.callback import guide_done, guide_failed
    from ai_worker.models import MedicalRecord, User

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

    # RAG 검색
    rag_context = search_text_for_medications(medications)

    try:
        # 1차: 복약 + 생활 가이드 생성
        response = _get_llm().invoke(
            [
                SystemMessage(content=GUIDE_SYSTEM),
                HumanMessage(content=build_guide_user_prompt(medications, user_health, rag_context)),
            ]
        )
        parsed = _parse_and_validate_guide(response.content)

        if parsed is None:
            raise ValueError("LLM 응답을 JSON으로 파싱할 수 없습니다.")

        # 2차: 약물 상호작용 전용 분석 (2종 이상인 경우)
        if len(medications) >= 2:
            interaction_result = _check_interactions(medications, user_health)
            if interaction_result:
                # 기존 파싱 결과에 상호작용 정보 병합
                existing = parsed.get("drug_interactions", [])
                new_interactions = interaction_result.get("interactions", [])
                # 중복 제거 후 병합
                merged = _merge_interactions(existing, new_interactions)
                parsed["drug_interactions"] = merged

                urgent = interaction_result.get("urgent_warnings", [])
                if urgent:
                    parsed["urgent_warnings"] = urgent
                    logger.warning(f"[generate_guide] 긴급 경고 발생 guide_id={guide_id}: {urgent}")

        summary_text = (parsed.get("summary") or "").strip()

        medication_guide = parsed.get("medication_guide")
        lifestyle_guide = parsed.get("lifestyle_guide")

        ok = guide_done(
            guide_id=guide_id,
            user_id=user_id,
            medication_guide=medication_guide,
            lifestyle_guide=lifestyle_guide,
            summary_text=summary_text,
            allergy_warnings=parsed.get("allergy_warnings", []),
            condition_interactions=parsed.get("condition_interactions", []),
            # 신규 필드 (콜백에서 선택적 처리)
            drug_interactions=parsed.get("drug_interactions", []),
            side_effects_watch=parsed.get("side_effects_watch", []),
            medication_schedule=parsed.get("medication_schedule", []),
            urgent_warnings=parsed.get("urgent_warnings", []),
        )
        if not ok:
            raise RuntimeError("guide_done callback 실패")

        logger.info(f"[generate_guide] 완료 guide_id={guide_id}")

    except Exception as exc:
        guide_failed(guide_id, user_id)
        logger.error(f"[generate_guide] 실패: {exc}", exc_info=True)
        # 지수 백오프: 30s, 60s, 120s
        countdown = 30 * (2**task.request.retries)
        raise task.retry(exc=exc, countdown=countdown) from exc


def _check_interactions(medications: list, user_health: dict) -> dict | None:
    """약물 상호작용 전용 LLM 분석."""
    try:
        response = _get_llm().invoke(
            [
                SystemMessage(content=INTERACTION_CHECK_SYSTEM),
                HumanMessage(content=build_interaction_check_prompt(medications, user_health)),
            ]
        )
        return _parse_json(response.content)
    except Exception as exc:
        logger.warning(f"[interaction_check] 실패 (무시): {exc}")
        return None


def _merge_interactions(existing: list, new_items: list) -> list:
    """기존 상호작용 목록과 새 목록을 중복 없이 병합."""
    seen = set()
    merged = []
    for item in existing + new_items:
        key = frozenset([item.get("drug_a", ""), item.get("drug_b", "")])
        if key not in seen:
            seen.add(key)
            merged.append(item)
    return merged


def _format_lifestyle_guide(guide_dict: dict) -> str:
    """lifestyle_guide dict → 포맷된 텍스트 변환."""
    sections = {
        "diet": "🍽️ 식이 지침",
        "exercise": "🏃 운동 지침",
        "sleep": "😴 수면 지침",
        "alcohol_smoking": "🚭 음주·흡연",
        "monitoring": "🔍 관찰 증상",
    }
    lines = []
    for key, label in sections.items():
        if guide_dict.get(key):
            lines.append(f"**{label}**\n{guide_dict[key]}")
    return "\n\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# 챗봇 태스크 (개선)
# ─────────────────────────────────────────────────────────────────


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


async def _do_process_chat(task, session_id: int, message_id: int, user_id: int, user_message: str):  # noqa: C901
    from ai_worker.models import ChatMessage, ChatSession, User
    from ai_worker.services.disease_code_service import lookup_disease_name_async

    try:
        user = await User.get_or_none(id=user_id)
        user_health = await load_user_health(user_id, user)

        # ── 현재 세션의 진료기록 + HIRA API 진단명 조회 ──────────
        current_record = None
        disease_name = None
        try:
            session = await ChatSession.get_or_none(id=session_id)
            if session and session.record_id:
                from ai_worker.models import MedicalRecord

                record = await MedicalRecord.get_or_none(id=session.record_id)
                if record and record.parsed_data:
                    disease_code = record.parsed_data.get("disease_code")
                    current_record = {
                        "disease_code": disease_code,
                        "medications": record.parsed_data.get("medications", []),
                        "hospital_name": record.parsed_data.get("hospital_name"),
                        "prescription_date": record.parsed_data.get("prescription_date"),
                    }

                    # HIRA API로 정확한 진단명 조회
                    if disease_code:
                        disease_name = await lookup_disease_name_async(disease_code)
                        logger.info(
                            f"[chat] HIRA 진단명 조회 완료 {disease_code} → {disease_name} session={session_id}"
                        )

        except Exception as rec_exc:
            logger.warning(f"[chat] 진료기록/HIRA 조회 실패 (무시): {rec_exc}")
        # ──────────────────────────────────────────────────────────

        if _is_off_topic(user_message):
            answer = (
                "MediLog 복약 도우미입니다. 의약품 복용, 건강 관리, 약물 상호작용, "
                "부작용 등 의약·건강 관련 질문만 답변드릴 수 있어요. "
                "궁금한 복약 정보가 있으시면 편하게 물어보세요! 😊"
            )
            _save_and_publish(session_id, message_id, user_message, answer)
            await ChatMessage.filter(id=message_id).update(content=answer, status="DONE")
            return

        rag_docs, rag_used = search_docs_with_scores(user_message)
        history = _get_history(session_id)

        # HIRA API로 조회한 disease_name 전달
        system_prompt = build_chat_system_prompt(
            user_health,
            rag_docs,
            current_record=current_record,
            disease_name=disease_name,
        )

        messages = [SystemMessage(content=system_prompt)]
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
            full_response += "\n\n*참고 문서 없음 — AI 일반 지식 기반 답변입니다. 중요한 사항은 약사에게 확인하세요.*"

        warning = _drug_interaction_check(user_message, user_health)
        if warning:
            full_response += f"\n\n⚠️ **주의**: {warning}"

        _save_and_publish(session_id, message_id, user_message, full_response)
        await ChatMessage.filter(id=message_id).update(content=full_response, status="DONE")

    except Exception as exc:
        _redis.publish(
            f"chat:stream:{session_id}",
            json.dumps({"error": str(exc), "message_id": message_id, "done": True}),
        )
        logger.error(f"[chat] 실패: {exc}", exc_info=True)
        raise task.retry(exc=exc) from exc


# ─────────────────────────────────────────────────────────────────
# 일일 건강 팁 태스크 (개선: 한국어 + 개인화)
# ─────────────────────────────────────────────────────────────────


@celery_app.task(bind=True, name="ai_worker.tasks.llm_task.generate_daily_tip_task", max_retries=2)
def generate_daily_tip_task(self, tip_id: str, user_id: int):
    logger.info(f"[daily_tip] tip_id={tip_id} user_id={user_id}")
    asyncio.run(_do_generate_daily_tip(self, tip_id, user_id))


async def _do_generate_daily_tip(task, tip_id: str, user_id: int):
    from tortoise import Tortoise

    user_health = {}
    if user_id and user_id > 0:
        try:
            await Tortoise.init(db_url=_db_url(), modules={"models": ["ai_worker.models"]})
            try:
                from ai_worker.models import User

                user = await User.get_or_none(id=user_id)
                user_health = await load_user_health(user_id, user)
            finally:
                await Tortoise.close_connections()
        except Exception as exc:
            logger.warning(f"[daily_tip] 사용자 정보 로드 실패 (기본값 사용): {exc}")

    # 계절 자동 판단
    month = datetime.now().month
    season = (
        "봄" if month in (3, 4, 5) else "여름" if month in (6, 7, 8) else "가을" if month in (9, 10, 11) else "겨울"
    )

    try:
        response = _get_llm().invoke(
            [
                SystemMessage(
                    content=(
                        "당신은 한국의 건강 전문가입니다. "
                        "반드시 순수 JSON만 출력하고 마크다운 코드 펜스를 사용하지 마세요."
                    )
                ),
                HumanMessage(
                    content=(
                        f"오늘 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}\n"
                        + build_daily_tip_prompt(user_health or None, season)
                    )
                ),
            ]
        )
        tip_data = _parse_json(response.content)

        # 응답 검증
        required_keys = {"title", "subtitle", "body", "highlight", "category"}
        if tip_data is None or not required_keys.issubset(tip_data.keys()):
            raise ValueError(f"daily_tip 응답 키 부족: {tip_data}")

        _redis.set(f"daily_tip:{tip_id}", json.dumps(tip_data, ensure_ascii=False), ex=86400)

        # 개인화 팁인 경우 user_id별 캐시에도 저장
        if user_id and user_id > 0:
            _redis.set(
                f"daily_tip:user:{user_id}",
                json.dumps(tip_data, ensure_ascii=False),
                ex=86400,
            )

        logger.info(f"[daily_tip] 완료 tip_id={tip_id} category={tip_data.get('category')}")

    except Exception as exc:
        logger.error(f"[daily_tip] 실패: {exc}", exc_info=True)
        raise task.retry(exc=exc, countdown=60) from exc


@celery_app.task(name="ai_worker.tasks.llm_task.generate_daily_tip_scheduled")
def generate_daily_tip_scheduled():
    """스케줄 기반 일일 팁 생성 (전체 사용자 공통)."""
    import uuid

    tip_id = str(uuid.uuid4())
    generate_daily_tip_task.apply_async(
        kwargs={"tip_id": tip_id, "user_id": 0},
        queue="llm",
    )


# ─────────────────────────────────────────────────────────────────
# 신규: 약물 상호작용 전용 태스크
# ─────────────────────────────────────────────────────────────────


@celery_app.task(
    bind=True,
    name="ai_worker.tasks.llm_task.check_drug_interactions_task",
    max_retries=2,
    default_retry_delay=10,
)
def check_drug_interactions_task(self, user_id: int, medications: list) -> dict:
    """
    약물 상호작용만 전용으로 빠르게 분석하는 태스크.
    가이드 생성 없이 상호작용만 필요할 때 사용.
    """
    logger.info(f"[interaction_check] user_id={user_id} drugs={len(medications)}종")
    try:
        user_health = asyncio.run(_load_health_only(user_id))
        result = _check_interactions(medications, user_health)
        if result is None:
            raise ValueError("상호작용 분석 실패")
        logger.info(f"[interaction_check] 완료 risk={result.get('overall_risk')}")
        return result
    except Exception as exc:
        logger.error(f"[interaction_check] 실패: {exc}", exc_info=True)
        raise self.retry(exc=exc) from exc


async def _load_health_only(user_id: int) -> dict:
    """사용자 건강 정보만 로드 (가이드 생성 없이)."""
    from tortoise import Tortoise

    from ai_worker.models import User

    await Tortoise.init(db_url=_db_url(), modules={"models": ["ai_worker.models"]})
    try:
        user = await User.get_or_none(id=user_id)
        return await load_user_health(user_id, user)
    finally:
        await Tortoise.close_connections()


# ─────────────────────────────────────────────────────────────────
# 유틸리티
# ─────────────────────────────────────────────────────────────────

# 개선: 확장된 오프토픽 키워드 + 한국어 의료 키워드 허용 목록
_OFF_TOPIC_KEYWORDS = {
    "en": ["stock", "crypto", "weather", "sports", "game", "politics", "entertainment"],
    "ko": [
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
        "부동산",
        "음악",
        "드라마",
    ],
}

_MEDICAL_KEYWORDS = [
    "약",
    "복용",
    "처방",
    "부작용",
    "건강",
    "병원",
    "의사",
    "약사",
    "질환",
    "증상",
    "mg",
    "ml",
    "투약",
    "치료",
    "진단",
    "혈압",
    "혈당",
    "콜레스테롤",
    "알러지",
]


def _is_off_topic(message: str) -> bool:
    """
    개선: 의료 키워드가 포함된 경우 오프토픽으로 판단하지 않음.
    """
    # 의료 관련 키워드가 있으면 오프토픽 아님
    if any(kw in message for kw in _MEDICAL_KEYWORDS):
        return False

    all_off = _OFF_TOPIC_KEYWORDS["en"] + _OFF_TOPIC_KEYWORDS["ko"]
    return any(kw in message for kw in all_off)


# 개선: 더 많은 약물-질환 위험 조합 커버
_DRUG_CONDITION_DANGER_MAP = {
    "아스피린": ["혈우병", "위궤양", "출혈성 질환", "임신 3분기"],
    "이부프로펜": ["신부전", "고혈압", "심부전", "위궤양"],
    "메트포르민": ["신부전", "간부전", "심부전"],
    "아목시실린": ["페니실린 알러지"],
    "세티리진": ["신부전", "녹내장"],
    "아토르바스타틴": ["간질환", "근육병증"],
    "암로디핀": ["대동맥협착증"],
}


def _drug_interaction_check(message: str, user_health: dict) -> str | None:
    """개선된 약물-기저질환 위험 체크."""
    conditions = [c["name"] for c in user_health.get("conditions", [])]
    allergies = [a["name"] for a in user_health.get("allergies", [])]
    all_conditions = conditions + allergies

    for drug, danger_conditions in _DRUG_CONDITION_DANGER_MAP.items():
        if drug in message:
            for dc in danger_conditions:
                if any(dc in cond for cond in all_conditions):
                    return (
                        f"**{drug}** 복용 시 **{dc}** 환자는 주의가 필요합니다. "
                        "반드시 처방 의사 또는 약사에게 알러지·기저질환 이력을 알려주세요."
                    )
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
    """LLM 응답 문자열 → JSON dict 파싱."""
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.removeprefix("```json").removeprefix("```")
        clean = clean.removesuffix("```").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        logger.error(f"[_parse_json] JSON 파싱 실패. 앞 200자: {clean[:200]!r}")
        return None


def _parse_and_validate_guide(raw: str) -> dict | None:
    """
    가이드 응답 파싱 + 필수 키 검증.

    필수 키가 없으면 None 반환 (guide_failed 처리).
    """
    parsed = _parse_json(raw)
    if parsed is None:
        return None

    required_keys = {"medication_guide", "summary"}
    missing = required_keys - parsed.keys()
    if missing:
        logger.error(f"[_parse_and_validate_guide] 필수 키 누락: {missing}")
        return None

    return parsed


# ai_worker/tasks/llm_task.py 파일 끝에 추가
@celery_app.task(
    name="ai_worker.tasks.llm_task.check_and_send_notifications",
    bind=True,
    max_retries=3,
)
def check_and_send_notifications(self):
    """Celery Beat 주기 태스크: 복약 알림 발송 (매 분 실행)"""
    asyncio.run(_do_check_notifications())


async def _do_check_notifications():
    from datetime import datetime, timedelta

    from tortoise import Tortoise

    await Tortoise.init(
        db_url=_db_url(),
        modules={"models": ["ai_worker.models"]},
    )
    try:
        from ai_worker.models import Notification

        now = datetime.now(UTC)
        trigger_window = (now + timedelta(minutes=10)).time()
        now_time = now.time()

        due = await Notification.filter(
            is_active=True,
            scheduled_time__gte=now_time,
            scheduled_time__lte=trigger_window,
        )

        for notif in due:
            logger.info(f"[notification] 알림 트리거: user_id={notif.user_id} title={notif.title} type={notif.type}")

    finally:
        await Tortoise.close_connections()
