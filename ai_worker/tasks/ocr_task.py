import asyncio
import logging
import re

from celery import Task, shared_task
from openai import OpenAI

from ai_worker.core.config import Config
from ai_worker.ocr import get_ocr_provider
from ai_worker.schemas.record_schemas import OcrTaskResult, ParsedRecord

logger = logging.getLogger(__name__)
_config = Config()  # type: ignore[call-arg]
_client = OpenAI(api_key=_config.OPENAI_API_KEY)

_PARSE_SYSTEM_PROMPT = (
    "당신은 의약품 처방전 및 약봉투 OCR 텍스트를 분석하는 전문가입니다. "
    "주어진 텍스트에서 정보를 추출하여 지정된 JSON 스키마에 맞게 반환하세요. "
    "확인할 수 없는 값은 null로 반환하세요.\n\n"
    "질병분류기호(disease_code) 추출 규칙:\n"
    "- 형식: 영문자 1자리 + 숫자 2자리 + 선택적으로 소수점 + 숫자 1~2자리 (예: J18.0, K29.10, N30)\n"
    "- OCR 오류 보정: 공백 제거, 숫자 자리의 'o'/'O'는 '0'으로, 'l'/'I'는 '1'으로 교체\n"
    "- 처방전에 없거나 불확실하면 null로 반환하세요."
)


_DISEASE_CODE_RE = re.compile(r"^[A-Z]\d{2}(\.\d{1,2})?$")


def _normalize_disease_code(code: str | None) -> str | None:
    if not code:
        return None
    s = code.replace(" ", "").strip()
    if not s or not s[0].isalpha():
        return None
    normalized = s[0].upper()
    for ch in s[1:]:
        if ch in ("o", "O"):
            normalized += "0"
        elif ch in ("l", "I", "|"):
            normalized += "1"
        else:
            normalized += ch
    if _DISEASE_CODE_RE.fullmatch(normalized):
        return normalized
    # 패턴 불일치라도 공백·대소문자만 정리한 값을 돌려줘 사용자가 폼에서 수정 가능하게
    return s[0].upper() + s[1:] if s else None


class OcrTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"[OCR Task] 최종 실패 task_id={task_id}: {exc}")
        record_id = args[0] if args else None
        if record_id:
            asyncio.run(_update_status(record_id, "FAILED"))
        super().on_failure(exc, task_id, args, kwargs, einfo)


@shared_task(
    base=OcrTask,
    bind=True,
<<<<<<< HEAD
    name="ai_worker.tasks.ocr_task.process_ocr",   # task → tasks
=======
    name="ai_worker.tasks.ocr_task.process_ocr",
>>>>>>> 36105e165a0efff5a62b5b145da53ee37f206d23
    max_retries=3,
)
def process_ocr(self, record_id: str, file_path: str) -> dict:
    try:
        raw_text = asyncio.run(_run_ocr(file_path))
        parsed = _parse_with_openai(raw_text)
        asyncio.run(_update_db(record_id, raw_text, parsed))
        logger.info(f"[OCR Task] 완료 record_id={record_id}")
        return OcrTaskResult(record_id=record_id, parsed_data=parsed.model_dump()).model_dump()
    except Exception as exc:
        logger.warning(f"[OCR Task] 재시도 {self.request.retries + 1}/3: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=5 * (2**self.request.retries)) from exc


async def _run_ocr(file_path: str) -> str:
    provider = get_ocr_provider(_config)
    raw_text = await provider.extract_text(file_path)
    logger.info(f"[OCR Task] 텍스트 추출 완료: {len(raw_text)}자")
    return raw_text


def _parse_with_openai(raw_text: str) -> ParsedRecord:
    response = _client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _PARSE_SYSTEM_PROMPT},
            {"role": "user", "content": f"다음 OCR 텍스트를 분석해주세요:\n\n{raw_text}"},
        ],
        response_format=ParsedRecord,
        temperature=0.2,  # 정보 추출 목적이므로 낮게 설정 — 추후 실험을 통해 개선 가능
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        logger.warning("[OCR Task] OpenAI 파싱 결과 없음, 빈 ParsedRecord 반환")
        return ParsedRecord()
    parsed.disease_code = _normalize_disease_code(parsed.disease_code)
    logger.info(f"[OCR Task] 파싱 완료: 약품 {len(parsed.medications)}개, 질병분류기호={parsed.disease_code}")
    return parsed


def _db_url() -> str:
    return f"mysql://{_config.DB_USER}:{_config.DB_PASSWORD}@{_config.DB_HOST}:{_config.DB_PORT}/{_config.DB_NAME}"


async def _update_db(record_id: str, ocr_raw_text: str, parsed: ParsedRecord) -> None:
    """
    [12] FastAPI callback 엔드포인트로 DB 저장 위임.
    동기 httpx 호출 — asyncio.run() 컨텍스트에서 실행됨.
    """
    from ai_worker.callback import ocr_done

    ocr_done(record_id, ocr_raw_text, parsed.model_dump())
    logger.info(f"[OCR Task] callback 전송 완료 record_id={record_id}")


async def _update_status(record_id: str, status: str) -> None:
    from ai_worker.callback import ocr_failed

    if status == "FAILED":
        ocr_failed(record_id)
