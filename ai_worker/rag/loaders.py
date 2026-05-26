"""data/rag 외부 파일(CSV·JSON·TXT) → Document 로드."""

import csv
import json
from pathlib import Path
from typing import Any

CONTENT_FIELDS = ("content", "text", "body")


def _make_document(content: str, metadata: dict) -> Any:
    from langchain_core.documents import Document

    return Document(page_content=content, metadata=metadata)


def _row_to_document(row: dict, source: str) -> Any | None:
    content = next((str(row[k]).strip() for k in CONTENT_FIELDS if row.get(k)), "")
    if not content:
        return None
    meta = {"source": source, **{k: v for k, v in row.items() if k not in CONTENT_FIELDS and v not in (None, "")}}
    return _make_document(content, meta)


def load_documents_from_csv(path: Path) -> list[Any]:
    """CSV: content/text/body 컬럼 필수, 나머지 컬럼은 metadata."""
    docs: list[Any] = []
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            doc = _row_to_document(row, path.name)
            if doc:
                docs.append(doc)
    return docs


def load_documents_from_json(path: Path) -> list[Any]:
    """JSON: [{...}] 또는 {"documents": [...]}. 각 항목은 content/text/body 필드."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("documents", raw) if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        raise ValueError(f"JSON must be a list or {{documents: [...]}}: {path}")

    docs: list[Any] = []
    for i, item in enumerate(rows):
        row = {"content": item} if isinstance(item, str) else item
        if not isinstance(row, dict):
            continue
        doc = _row_to_document(row, f"{path.name}#{i}")
        if doc:
            docs.append(doc)
    return docs


def load_documents_from_txt(path: Path) -> list[Any]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    return [_make_document(text, {"source": path.name})]


def load_documents_from_rag_dir(source_dir: Path) -> list[Any]:
    """data/rag 내 .csv, .json, .txt 파일을 모두 로드."""
    if not source_dir.is_dir():
        return []

    loaders = {
        ".csv": load_documents_from_csv,
        ".json": load_documents_from_json,
        ".txt": load_documents_from_txt,
    }
    docs: list[Any] = []
    for path in sorted(source_dir.iterdir()):
        if path.is_file() and (fn := loaders.get(path.suffix.lower())):
            docs.extend(fn(path))
    return docs
