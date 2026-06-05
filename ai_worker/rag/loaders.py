"""
개선된 data/rag 외부 파일(CSV·JSON·TXT) → Document 로드

변경 사항:
1. 청크 분할 (RecursiveCharacterTextSplitter) — 긴 문서를 적절한 크기로 분할하여
   임베딩 품질 향상 (너무 긴 문서는 임베딩 벡터가 평균화되어 특정 정보가 희석됨)
2. category 메타데이터 자동 추출 — drug_name 기반 약물 분류 태깅
3. 빈 content 및 예시 데이터 자동 필터링 ("의약 지식 본문을 여기에 작성" 등)
4. TXT 파일: 문단 단위 분할 지원
5. 로드 결과 통계 로깅
"""

import csv
import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CONTENT_FIELDS = ("content", "text", "body")

# 예시/더미 데이터 필터 패턴
_DUMMY_PATTERNS = [
    "의약 지식 본문",
    "약품명",
    "출처",
    "여기에 작성",
    "example",
    "placeholder",
]

# 청크 설정 (임베딩 품질 최적화)
CHUNK_SIZE = 400  # 문자 단위 (한국어 기준 약 200단어)
CHUNK_OVERLAP = 60  # 청크 간 겹침 (문맥 연속성 보장)

# 약물 카테고리 자동 분류 맵
_DRUG_CATEGORY_MAP = {
    "아스피린": "해열진통제",
    "타이레놀": "해열진통제",
    "아세트아미노펜": "해열진통제",
    "이부프로펜": "소염진통제",
    "나프록센": "소염진통제",
    "암로디핀": "고혈압치료제",
    "로사르탄": "고혈압치료제",
    "메트포르민": "당뇨치료제",
    "인슐린": "당뇨치료제",
    "아목시실린": "항생제",
    "세프트리악손": "항생제",
    "오메프라졸": "위장약",
    "란소프라졸": "위장약",
    "아토르바스타틴": "고지혈증치료제",
    "로수바스타틴": "고지혈증치료제",
    "세티리진": "항히스타민제",
    "로라타딘": "항히스타민제",
    "생활습관": "생활습관",
    "고혈압": "생활습관",
    "당뇨": "생활습관",
}


# ─────────────────────────────────────────────────────────────────
# 핵심 변환
# ─────────────────────────────────────────────────────────────────


def _make_document(content: str, metadata: dict) -> Any:
    from langchain_core.documents import Document

    return Document(page_content=content, metadata=metadata)


def _is_dummy(content: str) -> bool:
    """예시/더미 데이터 여부 판단."""
    lower = content.lower()
    return any(p.lower() in lower for p in _DUMMY_PATTERNS)


def _infer_category(row: dict) -> str:
    """drug_name 또는 content에서 카테고리 자동 추론."""
    combined = " ".join(
        [
            str(row.get("drug_name", "")),
            str(row.get("content", "")),
            str(row.get("category", "")),
        ]
    )
    for keyword, category in _DRUG_CATEGORY_MAP.items():
        if keyword in combined:
            return category
    return "기타"


def _row_to_documents(row: dict, source: str) -> list[Any]:
    """
    단일 row → Document 리스트 (청크 분할 포함).

    개선:
    - 더미 데이터 필터링
    - category 메타데이터 자동 추가
    - 긴 content는 CHUNK_SIZE 단위로 분할
    """
    content = next((str(row[k]).strip() for k in CONTENT_FIELDS if row.get(k)), "")
    if not content or _is_dummy(content):
        return []

    meta = {
        "source": row.get("source", source),
        "drug_name": row.get("drug_name", ""),
        "category": row.get("category") or _infer_category(row),
        **{
            k: v
            for k, v in row.items()
            if k not in (*CONTENT_FIELDS, "source", "drug_name", "category") and v not in (None, "")
        },
    }

    # 짧은 문서는 그대로, 긴 문서는 청크 분할
    if len(content) <= CHUNK_SIZE:
        return [_make_document(content, meta)]

    chunks = _split_text(content)
    docs = []
    for i, chunk in enumerate(chunks):
        chunk_meta = {**meta, "chunk_index": i, "chunk_total": len(chunks)}
        docs.append(_make_document(chunk, chunk_meta))
    return docs


def _split_text(text: str) -> list[str]:
    """
    한국어 친화적 청크 분할.

    우선순위: 문단(\n\n) → 문장(。.!) → CHUNK_SIZE 강제 분할
    """
    # 문단 단위 먼저 시도
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    if len(paragraphs) > 1:
        chunks = _merge_paragraphs(paragraphs)
        if chunks:
            return chunks

    # 문장 단위 분할 (한국어: 다/요/습니다 등 문말 기준)
    sentences = re.split(r"(?<=[다요니])\s+", text)
    if len(sentences) > 1:
        return _merge_sentences(sentences)

    # 강제 분할 (문장 구분 불가 시)
    return [text[i : i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP)]


def _merge_paragraphs(paragraphs: list[str]) -> list[str]:
    """문단들을 CHUNK_SIZE 이하로 합쳐 청크 생성."""
    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) + 2 > CHUNK_SIZE and current:
            chunks.append(current.strip())
            current = p
        else:
            current = (current + "\n\n" + p).strip() if current else p
    if current:
        chunks.append(current.strip())
    return chunks or ["\n\n".join(paragraphs)]


def _merge_sentences(sentences: list[str]) -> list[str]:
    """문장들을 CHUNK_SIZE 이하로 합쳐 청크 생성 (CHUNK_OVERLAP 적용)."""
    chunks, current = [], ""
    overlap_buf = ""
    for s in sentences:
        candidate = (current + " " + s).strip() if current else s
        if len(candidate) > CHUNK_SIZE and current:
            chunks.append(current.strip())
            overlap_buf = current[-CHUNK_OVERLAP:] if len(current) > CHUNK_OVERLAP else current
            current = (overlap_buf + " " + s).strip()
        else:
            current = candidate
    if current:
        chunks.append(current.strip())
    return chunks or sentences


# ─────────────────────────────────────────────────────────────────
# 파일 타입별 로더
# ─────────────────────────────────────────────────────────────────


def load_documents_from_csv(path: Path) -> list[Any]:
    """
    CSV 로드.
    필수: content/text/body 컬럼 중 하나
    선택: drug_name, category, source 등 → metadata
    """
    docs: list[Any] = []
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            docs.extend(_row_to_documents(row, path.name))
    logger.debug("CSV '%s': %d개 Document 로드", path.name, len(docs))
    return docs


def load_documents_from_json(path: Path) -> list[Any]:
    """
    JSON 로드.
    형식: [{...}] 또는 {"documents": [...]}
    각 항목은 content/text/body 필드 필수
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("documents", raw) if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        raise ValueError(f"JSON must be a list or {{documents: [...]}}: {path}")

    docs: list[Any] = []
    for i, item in enumerate(rows):
        row = {"content": item} if isinstance(item, str) else item
        if not isinstance(row, dict):
            continue
        docs.extend(_row_to_documents(row, f"{path.name}#{i}"))
    logger.debug("JSON '%s': %d개 Document 로드", path.name, len(docs))
    return docs


def load_documents_from_txt(path: Path) -> list[Any]:
    """
    TXT 로드.
    개선: 문단 단위 분할 지원 (기존: 파일 전체를 단일 Document)
    """
    text = path.read_text(encoding="utf-8").strip()
    if not text or _is_dummy(text):
        return []

    # 문단 단위 분할
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    if len(paragraphs) <= 1:
        return [_make_document(text, {"source": path.name, "category": "기타"})]

    docs = []
    for i, para in enumerate(paragraphs):
        if len(para) < 20:  # 너무 짧은 문단 건너뜀
            continue
        docs.append(
            _make_document(
                para,
                {"source": path.name, "category": "기타", "paragraph_index": i},
            )
        )
    logger.debug("TXT '%s': %d개 Document 로드", path.name, len(docs))
    return docs


def load_documents_from_rag_dir(source_dir: Path) -> list[Any]:
    """
    data/rag 내 .csv, .json, .txt 파일을 모두 로드.
    개선: .example 파일 자동 제외, 로드 통계 출력
    """
    if not source_dir.is_dir():
        logger.warning("RAG 소스 디렉터리 없음: %s", source_dir)
        return []

    loaders = {
        ".csv": load_documents_from_csv,
        ".json": load_documents_from_json,
        ".txt": load_documents_from_txt,
    }

    docs: list[Any] = []
    skipped: list[str] = []

    for path in sorted(source_dir.iterdir()):
        if not path.is_file():
            continue
        # .example 파일 제외 ("knowledge.json.example" 등)
        if ".example" in path.name:
            skipped.append(path.name)
            continue
        loader = loaders.get(path.suffix.lower())
        if loader:
            batch = loader(path)
            docs.extend(batch)
            logger.info("RAG 로드: '%s' → %d개", path.name, len(batch))
        else:
            skipped.append(path.name)

    if skipped:
        logger.debug("RAG 건너뜀: %s", skipped)
    logger.info("RAG 총 로드: %d개 Document (%s)", len(docs), source_dir)
    return docs
