"""KCD(한국표준질병사인분류) 코드 검증 모듈."""

import csv
import os
import re

# {코드: [주명칭, 동의어1, 동의어2, ...]} — 첫 번째가 공식 주명칭
_KCD_DICT: dict[str, list[str]] | None = None

_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "kcd", "건강보험심사평가원_상병마스터.csv")

_KCD_PATTERN = re.compile(r"(?<![A-Za-z\d])[A-Z]\d{2,4}(?![A-Za-z\d])")


def _load() -> dict[str, list[str]]:
    global _KCD_DICT
    if _KCD_DICT is None:
        data: dict[str, list[str]] = {}
        with open(_CSV_PATH, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                code = row["상병기호"].strip()
                name = row["한글명"].strip()
                if code and name:
                    if code not in data:
                        data[code] = [name]
                    else:
                        data[code].append(name)
        _KCD_DICT = data
    return _KCD_DICT


def lookup(message: str) -> dict[str, str]:
    """메시지에서 KCD 코드를 감지하고 {코드: 주명칭} 반환."""
    kcd = _load()
    codes = _KCD_PATTERN.findall(message)
    return {code: kcd[code][0] for code in codes if code in kcd}


def synonyms(code: str) -> list[str]:
    """코드의 모든 동의어 반환 (주명칭 포함)."""
    kcd = _load()
    return kcd.get(code, [])
