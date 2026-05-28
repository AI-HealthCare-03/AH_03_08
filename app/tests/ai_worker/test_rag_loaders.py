"""RAG CSV/JSON/TXT 로더 테스트 (Chroma·langchain 불필요)."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_worker.rag import loaders

pytestmark = pytest.mark.no_db


@pytest.fixture(autouse=True)
def mock_document(monkeypatch):
    monkeypatch.setattr(
        loaders,
        "_make_document",
        lambda content, metadata: SimpleNamespace(page_content=content, metadata=metadata),
    )


def test_load_csv_and_json(tmp_path: Path):
    (tmp_path / "drugs.csv").write_text(
        "content,drug_name\n타이레놀 복용법,타이레놀\n",
        encoding="utf-8",
    )
    (tmp_path / "notes.json").write_text(
        '[{"text": "페니실린 알러지 주의", "severity": "high"}]',
        encoding="utf-8",
    )

    docs = loaders.load_documents_from_rag_dir(tmp_path)

    assert len(docs) == 2
    assert docs[0].page_content == "타이레놀 복용법"
    assert docs[0].metadata["drug_name"] == "타이레놀"
    assert docs[1].page_content == "페니실린 알러지 주의"
    assert docs[1].metadata["severity"] == "high"


def test_load_txt(tmp_path: Path):
    (tmp_path / "note.txt").write_text("복용 시간 안내", encoding="utf-8")

    docs = loaders.load_documents_from_txt(tmp_path / "note.txt")

    assert len(docs) == 1
    assert docs[0].page_content == "복용 시간 안내"


def test_load_json_documents_wrapper(tmp_path: Path):
    (tmp_path / "pack.json").write_text(
        '{"documents": [{"body": "복용 전 식사 여부 확인"}]}',
        encoding="utf-8",
    )

    docs = loaders.load_documents_from_json(tmp_path / "pack.json")

    assert len(docs) == 1
    assert docs[0].page_content == "복용 전 식사 여부 확인"


def test_skip_rows_without_content(tmp_path: Path):
    (tmp_path / "bad.csv").write_text("drug_name\nonly_meta\n", encoding="utf-8")

    assert loaders.load_documents_from_csv(tmp_path / "bad.csv") == []


def test_ignore_example_files(tmp_path: Path):
    (tmp_path / "knowledge.csv.example").write_text("content,x\nshould,skip\n", encoding="utf-8")

    assert loaders.load_documents_from_rag_dir(tmp_path) == []
