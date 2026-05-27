"""ChromaDB RAG — 벡터 저장·검색 (가이드·챗봇 공용)."""

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

COLLECTION_NAME = "medical_knowledge"
DEFAULT_PERSIST_DIR = "/data/chromadb"
DEFAULT_RELEVANCE_THRESHOLD = 0.6

_embeddings = None
_vectorstore = None


def get_vectorstore():
    """Chroma 벡터스토어 싱글톤 (실패 시 None)."""
    global _embeddings, _vectorstore
    if _vectorstore is not None:
        return _vectorstore
    try:
        from langchain_chroma import Chroma
        from langchain_openai import OpenAIEmbeddings

        _embeddings = OpenAIEmbeddings(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            
        )
        _vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=_embeddings,
            persist_directory=os.getenv("CHROMA_PERSIST_DIR", DEFAULT_PERSIST_DIR),
        )
    except Exception as exc:
        logger.warning("ChromaDB init failed: %s", exc)
        _vectorstore = None
    return _vectorstore


def search_text_for_medications(medications: list, *, k: int = 5) -> str:
    """가이드 프롬프트용 — 약품명으로 유사 문서 검색 후 텍스트 블록 반환."""
    if not medications:
        return ""
    query = " ".join(m.get("drug_name", "") for m in medications if m.get("drug_name"))
    if not query.strip():
        return ""
    try:
        vs = get_vectorstore()
        if not vs:
            return ""
        docs = vs.similarity_search(query, k=k)
        if not docs:
            return ""
        return "\n\n".join(f"[{i + 1}] {d.page_content}" for i, d in enumerate(docs))
    except Exception as exc:
        logger.warning("RAG search (medications) failed: %s", exc)
        return ""


def search_docs_with_scores(
    query: str,
    *,
    k: int = 3,
    threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
) -> tuple[list[Any], bool]:
    """챗봇용 — relevance score 필터 후 (문서 목록, RAG 사용 여부)."""
    if not query.strip():
        return [], False
    try:
        vs = get_vectorstore()
        if not vs:
            return [], False
        results = vs.similarity_search_with_relevance_scores(query, k=k)
        filtered = [doc for doc, score in results if score >= threshold]
        return filtered, bool(filtered)
    except Exception as exc:
        logger.warning("RAG search (chat) failed: %s", exc)
        return [], False


def ingest_text_documents(documents: list[Any]) -> int:
    """문서를 컬렉션에 추가. 성공 시 추가된 문서 수 반환."""
    if not documents:
        return 0
    vs = get_vectorstore()
    if not vs:
        raise RuntimeError("ChromaDB vectorstore is not available")
    vs.add_documents(documents)
    return len(documents)


def load_documents_from_dir(source_dir: Path) -> list[Any]:
    """data/rag 디렉터리에서 CSV·JSON·TXT 로드 (loaders 위임)."""
    from ai_worker.rag.loaders import load_documents_from_rag_dir

    return load_documents_from_rag_dir(source_dir)


def ingest_rag_from_dir(source_dir: Path) -> int:
    """data/rag 파일 로드 후 ChromaDB에 적재. 적재된 문서 수 반환."""
    docs = load_documents_from_dir(source_dir)
    return ingest_text_documents(docs)
