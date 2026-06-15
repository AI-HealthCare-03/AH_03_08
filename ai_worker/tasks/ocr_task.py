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
    "의약품(medications) 추출 규칙:\n"
    "- 처방전 의약품은 '[코드번호]약품명' 또는 '[구분][코드번호]약품명' 형식으로 식별됩니다.\n"
    "- 처방전 테이블이 열(컬럼) 단위로 OCR되어 숫자가 약품 코드 목록 앞뒤에 흩어집니다.\n"
    "\n"
    "  [테이블 OCR 패턴 — 필수 숙지]\n"
    "  처방전 첫 번째 약품의 1일횟수·투약일수는 약품 코드 목록 시작 전에 먼저 나오고,\n"
    "  나머지 약품들의 값은 약품 코드 목록 뒤에 순서대로 나옵니다.\n"
    "\n"
    "  예시 1 — 첫 약품만 횟수가 다른 경우:\n"
    "  '3 7 1.00 [V0130005]발트렉스정500mg [A1120005]셀레콕스캡슐200mg [M0110003]가스모틴정5mg 1.00 1.00 2 7 매식후30분 2 7'\n"
    "  → 발트렉스정: dosage=1, frequency=3, days=7  ← 코드 목록 앞 '3 7'\n"
    "  → 셀레콕스캡슐: dosage=1, frequency=2, days=7\n"
    "  → 가스모틴정: dosage=1, frequency=2, days=7\n"
    "\n"
    "  예시 2 — 약품마다 투약일수가 다른 경우:\n"
    "  '14 2 1 [A2130005]에이티피캡슐250mg [H0310001]하이티손크림1% [M0110003]마이렉스정5mg 1.00 1.00 1.00 2 1 취침전30분 매식후30분 환부도포 14'\n"
    "  → 에이티피캡슐: dosage=1, frequency=2, days=14  ← '14 2'가 days=14, freq=2\n"
    "  → 하이티손크림: dosage=1, frequency=2, days=1   ← 목록 뒤 '2 1'\n"
    "  → 마이렉스정:   dosage=1, frequency=1, days=14  ← '14 2 1'의 마지막 '1'이 freq, 맨 뒤 '14'가 days\n"
    "\n"
    "  예시 3 — 4개 약품, 수치가 앞뒤에 분산 + 총투약일수 순서가 뒤섞인 경우:\n"
    "  '1 3 \" 1 [11111]아목시실린...캡슐 [A1120005]셀레콕스캡슐 [M0110003]가스모틴정 [급여][454000276]오티플렉스점이액 3 1일 3회 식후 30분 복용 1일 4회 양안 점안. 1일 2회 환측 이강 점이. 7 5 5 10 4 1 2 1'\n"
    "  코드 목록 앞 '1 3': 아목시실린 dosage=1, frequency=3\n"
    "  코드 목록 앞 '\"': 셀레콕스 용법 생략 기호\n"
    "  코드 목록 앞 '1': 셀레콕스 dosage=1\n"
    "  코드 목록 바로 뒤 '3': 셀레콕스 frequency=3\n"
    "  끝 '7 5 5 10': 총투약일수 — 오티플렉스=7, 아목시실린=5, 셀레콕스=5, 가스모틴=10\n"
    "  끝 '4 1 2 1': 가스모틴 frequency=4·dosage=1, 오티플렉스 frequency=2·dosage=1\n"
    "  → 아목시실린: dosage=1, frequency=3, days=5\n"
    "  → 셀레콕스:   dosage=1, frequency=3, days=5\n"
    "  → 가스모틴:   dosage=1, frequency=4, days=10\n"
    "  → 오티플렉스: dosage=1, frequency=2, days=7\n"
    "\n"
    "- 1회량(dosage): 1회 복용 정수/포 수 (0.5~3 범위, 소수점 형태 1.00으로 표기되기도 함)\n"
    "- 1일횟수(frequency): 하루 복용 횟수 (1~4 범위의 정수)\n"
    "- 투약일수(days): 총 투약 일수 (1~90 범위의 정수, 약품마다 개별 값 — 1일치도 가능)\n"
    "- 모든 약품에 같은 값을 적용하지 말고, OCR 텍스트에서 각 약품의 숫자를 개별적으로 찾아 할당하세요.\n\n"
    "발행일(issued_at) 추출 규칙:\n"
    "- 처방전의 '교부년월일', '처방일', '처방일자', '발행일', '조제일' 등에서 추출하세요.\n"
    "- 형식: YYYY-MM-DD (예: 2024-03-15)\n"
    "- '2024년 3월 15일', '2024.03.15', '24/03/15' 등 다양한 형식을 YYYY-MM-DD로 변환하세요.\n\n"
    "처방의(doctor) 추출 규칙:\n"
    "- 처방전에 의사 이름이 명확히 표기된 경우에만 추출하세요.\n"
    "- 도장·서명만 있거나 불확실하면 반드시 null로 반환하세요.\n\n"
    "질병분류기호(disease_code) 추출 규칙:\n"
    "- 형식: 영문자 1자리 + 숫자 2~4자리 (예: J18, K291, N30, N300, H664)\n"
    "- 소수점은 제거하되 소수점 뒤 숫자는 유지하세요: N30.0 → N300, H66.4 → H664\n"
    "- OCR에 소수점이 없으면 절대 숫자를 추가하지 마세요: 'J 0 3' → 'J03' (J030 아님), 'N 3 0' → 'N30'\n"
    "- 처방전 양식에서 분류기호가 한 글자씩 빈칸이 있는 사각형 박스에 표시된 경우,\n"
    "  OCR이 'N 3 0 0' 형태로 읽힙니다. 공백을 모두 제거하여 'N300'으로 반환하세요.\n"
    "- OCR 오류 보정: 공백·소수점 제거, 숫자 자리의 'o'/'O'는 '0'으로, 'l'/'I'는 '1'으로 교체\n"
    "- [중요] 박스 형식에서 'J'(제이)가 'O'(영문 오)로 OCR 오인식되는 경우가 매우 흔합니다.\n"
    "  추출 코드가 O계열(산부인과)인데 처방 약품이 항생제·호흡기·이비인후과·피부과 계열이면,\n"
    "  첫 글자를 J로 교정하세요. 예: OCR='O030', 약품=아목시실린/편도염약 → disease_code='J03'\n"
    "- 처방전에 분류기호가 두 줄(두 코드)로 표시된 경우, 첫 번째 코드만 반환하세요.\n"
    "- 처방전에 없거나 불확실하면 null로 반환하세요."
)


_DISEASE_CODE_RE = re.compile(r"^[A-Z]\d{2,4}$")


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
    # CSV uses no-dot format (H664 not H66.4) — strip dot before validation
    no_dot = normalized.replace(".", "")
    if _DISEASE_CODE_RE.fullmatch(no_dot):
        from ai_worker.kcd import synonyms as kcd_synonyms

        if kcd_synonyms(no_dot):
            return no_dot
        logger.warning(f"[OCR Task] 질병분류기호 '{no_dot}' — KCD 사전에 없는 코드, 무시")
    return None


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
    name="ai_worker.tasks.ocr_task.process_ocr",  # task → tasks
    max_retries=3,
)
def process_ocr(self, record_id: str, file_path: str) -> dict:
    try:
        raw_text = asyncio.run(_run_ocr(file_path))
        parsed = _parse_with_openai(raw_text)
        asyncio.run(_enrich_medications(parsed))
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
    logger.info(f"[OCR Raw]\n{raw_text}")
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
    if parsed.disease_code:
        from ai_worker.kcd import synonyms as kcd_synonyms

        names = kcd_synonyms(parsed.disease_code)
        parsed.disease_name = names[0] if names else None
    else:
        parsed.disease_name = None
    logger.info(f"[OCR Task] 파싱 완료: 약품 {len(parsed.medications)}개, 질병분류기호={parsed.disease_code}")
    return parsed


async def _enrich_medications(parsed: ParsedRecord) -> None:
    from ai_worker.services.drug_lookup_service import correct_names_batch, lookup_drug

    # 1차 패스: MFDS API로 조회
    results = [await lookup_drug(med.name) for med in parsed.medications]

    # API 미매칭 약품만 모아서 GPT로 일괄 교정
    failed_idx = [i for i, r in enumerate(results) if not r["found"]]
    if failed_idx:
        failed_names = [parsed.medications[i].name for i in failed_idx]
        corrections = await correct_names_batch(failed_names)

        # 2차 패스: 교정된 이름으로 API 재조회
        for i in failed_idx:
            original = parsed.medications[i].name
            corrected = corrections.get(original)
            if corrected and corrected != original:
                recheck = await lookup_drug(corrected)
                if recheck["found"]:
                    results[i] = recheck
                    logger.info(f"[Enrich] '{original}' → GPT교정 '{corrected}' → API확인 ✓")

    # 결과 반영
    from ai_worker.services.drug_lookup_service import normalize_dosage_string

    for med, result in zip(parsed.medications, results, strict=False):
        med.name = result["item_name"] or med.name
        med.drug_class = result["class_name"]
        if result.get("dosage"):
            med.concentration = result["dosage"]  # API에서 정규화된 값
        elif med.concentration:
            med.concentration = normalize_dosage_string(med.concentration)  # GPT 추출값 단위 정규화, 용량 없으면 None


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
