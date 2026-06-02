"""Chroma RAG 검색·문서 로드 단위 테스트 (DB·실제 Chroma 불필요)."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from ai_worker.rag import chroma_store

pytestmark = pytest.mark.no_db


@pytest.fixture(autouse=True)
def reset_chroma_singleton():
    chroma_store._embeddings = None
    chroma_store._vectorstore = None
    yield
    chroma_store._embeddings = None
    chroma_store._vectorstore = None


def test_search_text_for_medications_empty_when_no_drugs():
    assert chroma_store.search_text_for_medications([]) == ""
    assert chroma_store.search_text_for_medications([{"dosage": "500mg"}]) == ""


def test_search_text_for_medications_formats_results():
    mock_vs = MagicMock()
    # Mock the correct method with (doc, score) tuples
    mock_vs.similarity_search_with_relevance_scores.return_value = [
        (SimpleNamespace(page_content="타이레놀 복용 주의", metadata={"source": "가이드"}), 0.92),
        (SimpleNamespace(page_content="간 손상 주의", metadata={"source": "가이드"}), 0.88),
    ]
    with patch.object(chroma_store, "get_vectorstore", return_value=mock_vs):
        text = chroma_store.search_text_for_medications([{"drug_name": "타이레놀"}])

    assert "[1] 타이레놀 복용 주의" in text
    assert "[2] 간 손상 주의" in text
    mock_vs.similarity_search_with_relevance_scores.assert_called_once()


def test_search_docs_with_scores_filters_by_threshold():
    mock_vs = MagicMock()
    # Mock MMR results (no scores)
    mock_vs.max_marginal_relevance_search.return_value = [
        SimpleNamespace(page_content="high"),
    ]
    # Mock similarity search for score mapping
    mock_vs.similarity_search_with_relevance_scores.return_value = [
        (SimpleNamespace(page_content="high"), 0.85),
        (SimpleNamespace(page_content="low"), 0.3),
    ]
    with patch.object(chroma_store, "get_vectorstore", return_value=mock_vs):
        docs, used = chroma_store.search_docs_with_scores("타이레놀 부작용")

    assert used is True
    assert len(docs) == 1
    assert docs[0].page_content == "high"


def test_search_docs_with_scores_no_vectorstore():
    with patch.object(chroma_store, "get_vectorstore", return_value=None):
        docs, used = chroma_store.search_docs_with_scores("질문")
    assert docs == []
    assert used is False


def test_ingest_rag_from_dir(tmp_path: Path):
    (tmp_path / "a.txt").write_text("문서 A", encoding="utf-8")

    with patch.object(chroma_store, "load_documents_from_dir") as load_mock:
        load_mock.return_value = [SimpleNamespace(page_content="문서 A")]
        with patch.object(chroma_store, "ingest_text_documents", return_value=1) as ingest_mock:
            count = chroma_store.ingest_rag_from_dir(tmp_path)

    assert count == 1
    load_mock.assert_called_once_with(tmp_path)
    ingest_mock.assert_called_once()
