import json
import logging
import re

import httpx

from ai_worker.core.config import config

logger = logging.getLogger(__name__)

_DRUG_API_URL = "http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService04/getDrugPrdtPrmsnDtlInq04"
_cache: dict[str, dict] = {}

# 숫자 + 단위 패턴 (그룹1: 숫자, 그룹2: 단위)
_DOSAGE_RE = re.compile(
    r"([\d.]+)\s*(밀리그램|밀리그람|마이크로그램|마이크로그람|그람|그래|mg|mcg|ug|μg|ml|mL|g|IU|단위|%)",
    re.IGNORECASE,
)
_NOISE_RE = re.compile(r"^[^가-힣a-zA-Z0-9]+")
_PARENS_RE = re.compile(r"\([^)]*\)")  # 괄호 안 제약사명 제거용

_UNIT_NORM: dict[str, str] = {
    "밀리그램": "mg",
    "밀리그람": "mg",
    "마이크로그램": "mcg",
    "마이크로그람": "mcg",
    "ug": "mcg",
    "μg": "mcg",
    "그람": "g",
    "그래": "g",
    "밀리리터": "mL",
    "ml": "mL",
}

_CORRECT_SYSTEM_PROMPT = (
    "다음은 처방전 OCR로 추출된 약품명 목록입니다. "
    "각 약품명의 OCR 오인식(글자 누락·오타·공백)을 교정하여 실제 한국 의약품 품목명에 가장 가까운 이름으로 반환하세요. "
    "용량(mg, 밀리그램 등)은 제외하고 약품명만 반환하세요. "
    "확실하지 않으면 원본 그대로 반환하세요. "
    'JSON 형식 {"원본명": "교정된명", ...} 으로만 응답하세요.'
)


def normalize_dosage_string(s: str) -> str | None:
    """
    문자열 어디서든 숫자+단위 패턴만 추출하여 정규화.
    '60밀리그램' → '60mg'
    '(모사프리드시트르산염수산화물)_(5.29mg/1정)' → '5.29mg'
    '(삼일제약)' → None  (용량 없음)
    """
    m = _DOSAGE_RE.search(s)
    if not m:
        return None
    std_unit = _UNIT_NORM.get(m.group(2).lower(), m.group(2))
    return f"{m.group(1)}{std_unit}"


def _clean_name(name: str) -> str:
    return _NOISE_RE.sub("", name).strip()


def _extract_dosage(name: str) -> tuple[str, str | None]:
    """
    이름에서 용량을 분리.
    '탐스폰서방정0.2밀리그램' → ('탐스폰서방정', '0.2mg')
    용량이 없으면 → (name, None)
    """
    m = _DOSAGE_RE.search(name)
    if not m:
        return name.strip(), None
    number = m.group(1)
    unit = m.group(2)
    std_unit = _UNIT_NORM.get(unit.lower(), unit)
    dosage = f"{number}{std_unit}"
    return name[: m.start()].strip(), dosage


async def lookup_drug(raw_name: str) -> dict:
    """
    약품명으로 MFDS 의약품 품목 허가 정보 API 조회.
    Returns: {"item_name": ..., "class_name": ..., "dosage": ..., "found": bool}
    """
    if not config.PUBLIC_DATA_API_KEY:
        _, ocr_dosage = _extract_dosage(raw_name)
        return {"item_name": raw_name, "class_name": None, "dosage": ocr_dosage, "found": False}

    clean = _clean_name(raw_name)
    if not clean:
        return {"item_name": raw_name, "class_name": None, "dosage": None, "found": False}

    search_name, ocr_dosage = _extract_dosage(clean)
    if not search_name:
        search_name = clean

    cache_key = search_name
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                _DRUG_API_URL,
                params={
                    "serviceKey": config.PUBLIC_DATA_API_KEY,
                    "itemName": search_name,
                    "numOfRows": "3",
                    "pageNo": "1",
                    "type": "json",
                },
            )

        if resp.status_code != 200:
            logger.warning(f"[Drug API] HTTP {resp.status_code} for '{search_name}'")
            return {"item_name": clean, "class_name": None, "dosage": ocr_dosage, "found": False}

        data = resp.json()
        items = (data.get("body") or {}).get("items") or []
        if not items:
            logger.info(f"[Drug API] 결과 없음: '{search_name}'")
            return {"item_name": clean, "class_name": None, "dosage": ocr_dosage, "found": False}

        item = items[0]
        api_item_name = item.get("itemName") or item.get("ITEM_NAME") or clean
        api_item_name = _PARENS_RE.sub("", api_item_name).strip()  # (삼일제약) 등 제거
        class_name = item.get("classnm") or item.get("CLASS_NM")

        clean_name, api_dosage = _extract_dosage(api_item_name)

        result = {
            "item_name": clean_name or search_name,
            "class_name": class_name,
            "dosage": api_dosage or ocr_dosage,
            "found": True,
        }
        _cache[cache_key] = result
        logger.info(f"[Drug API] '{raw_name}' → '{result['item_name']}' {result['dosage']} / {result['class_name']}")
        return result

    except Exception as exc:
        logger.warning(f"[Drug API] 조회 실패 '{search_name}': {exc}")
        return {"item_name": clean, "class_name": None, "dosage": ocr_dosage, "found": False}


async def correct_names_batch(names: list[str]) -> dict[str, str]:
    """
    OCR 오인식된 약품명들을 GPT로 일괄 교정.
    Returns: {"원본명": "교정된명", ...}
    """
    if not names:
        return {}

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

    names_text = "\n".join(f"- {n}" for n in names)
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _CORRECT_SYSTEM_PROMPT},
                {"role": "user", "content": names_text},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        result = json.loads(response.choices[0].message.content or "{}")
        logger.info(f"[Drug GPT] 교정 결과: {result}")
        return result
    except Exception as exc:
        logger.warning(f"[Drug GPT] 배치 교정 실패: {exc}")
        return {}
