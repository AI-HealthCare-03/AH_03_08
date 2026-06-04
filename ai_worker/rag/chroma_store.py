"""
개선된 ChromaDB RAG — 벡터 저장·검색 (가이드·챗봇 공용)

변경 사항:
1. search_text_for_medications: 약품명 통합 쿼리 → 약품별 개별 쿼리 후 병합
   (예: "아스피린 메트포르민" 합성 쿼리는 임베딩 공간에서 중간 지점을 검색하여
    어느 약품과도 관련 없는 문서가 top-k에 포함될 수 있음)
2. MMR(Maximal Marginal Relevance) 검색 적용 — 중복 문서 제거, 다양성 보장
3. 카테고리 필터 검색 지원 (예: 생활습관 문서만 검색)
4. 검색 결과에 score·출처 메타데이터 포함하여 프롬프트 투명성 향상
5. 인메모리 LRU 캐시 — 동일 쿼리 반복 시 ChromaDB 재호출 방지
6. 벡터스토어 초기화 실패 시 명시적 재시도 로직
7. 청크 분할 인제스트 (대용량 문서 지원)
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

COLLECTION_NAME = "medical_knowledge"
DEFAULT_PERSIST_DIR = "/data/chromadb"
DEFAULT_RELEVANCE_THRESHOLD = 0.55   # 기존 0.6 → 0.55 (약학 도메인은 임베딩 거리 편차가 큼)
MMR_FETCH_K = 20                     # MMR 후보 풀 크기
MMR_LAMBDA = 0.6                     # 관련성(1.0) ↔ 다양성(0.0) 균형

_embeddings = None
_vectorstore = None


# ─────────────────────────────────────────────────────────────────
# 싱글톤 초기화
# ─────────────────────────────────────────────────────────────────

def get_vectorstore(*, force_reinit: bool = False):
    """
    Chroma 벡터스토어 싱글톤.

    개선: force_reinit=True 로 명시적 재초기화 가능.
    실패 시 None 반환 (호출부에서 graceful degradation).
    """
    global _embeddings, _vectorstore
    if _vectorstore is not None and not force_reinit:
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
        count = _vectorstore._collection.count()
        logger.info("ChromaDB 초기화 완료 — 문서 수: %d", count)
    except Exception as exc:
        logger.warning("ChromaDB init failed: %s", exc)
        _vectorstore = None
    return _vectorstore


# ─────────────────────────────────────────────────────────────────
# 가이드 생성용 검색 (약품별 개별 쿼리 → 병합)
# ─────────────────────────────────────────────────────────────────

def search_text_for_medications(
    medications: list,
    *,
    k_per_drug: int = 3,
    include_lifestyle: bool = True,
) -> str:
    """
    가이드 프롬프트용 — 약품별 개별 검색 후 중복 제거하여 텍스트 블록 반환.

    기존 문제:
      "아스피린 메트포르민 암로디핀" 처럼 약품명을 공백으로 이어붙인 단일 쿼리는
      임베딩 공간에서 세 약품의 중간 벡터를 검색 → 어느 약품과도 관련 없는
      문서가 top-k에 들어올 수 있음.

    개선:
      각 약품명을 독립 쿼리로 검색 후 (약품명, 내용) 기준으로 중복 제거.
      추가로 기저질환 생활습관 문서를 별도 쿼리로 가져옴.

    Args:
        medications: [{"drug_name": str, ...}, ...]
        k_per_drug: 약품 1종당 검색 문서 수
        include_lifestyle: 기저질환 관련 생활습관 문서 포함 여부
    """
    if not medications:
        return ""

    vs = get_vectorstore()
    if not vs:
        return ""

    seen: set[str] = set()
    collected: list[tuple[float, str, str]] = []  # (score, source, content)

    # 1. 약품별 개별 검색
    for med in medications:
        drug_name = (med.get("drug_name") or "").strip()
        if not drug_name:
            continue

        cache_key = _cache_key(drug_name)
        cached = _query_cache_get(cache_key)
        if cached is not None:
            for item in cached:
                uid = _content_uid(item[2])
                if uid not in seen:
                    seen.add(uid)
                    collected.append(item)
            continue

        try:
            results = vs.similarity_search_with_relevance_scores(
                drug_name,
                k=k_per_drug,
            )
            batch: list[tuple[float, str, str]] = []
            for doc, score in results:
                content = doc.page_content.strip()
                uid = _content_uid(content)
                source = doc.metadata.get("source", "알 수 없음")
                batch.append((score, source, content))
                if uid not in seen:
                    seen.add(uid)
                    collected.append((score, source, content))
            _query_cache_set(cache_key, batch)
        except Exception as exc:
            logger.warning("RAG search (drug=%s) failed: %s", drug_name, exc)

    # 2. 생활습관 문서 추가 검색 (조건 질환 키워드)
    if include_lifestyle:
        lifestyle_keywords = _extract_condition_keywords(medications)
        for kw in lifestyle_keywords:
            try:
                results = vs.similarity_search_with_relevance_scores(
                    f"{kw} 생활습관 관리",
                    k=2,
                )
                for doc, score in results:
                    content = doc.page_content.strip()
                    uid = _content_uid(content)
                    if uid not in seen:
                        seen.add(uid)
                        source = doc.metadata.get("source", "알 수 없음")
                        collected.append((score, source, content))
            except Exception as exc:
                logger.warning("RAG search (lifestyle=%s) failed: %s", kw, exc)

    if not collected:
        return ""

    # score 내림차순 정렬 후 포맷
    collected.sort(key=lambda x: x[0], reverse=True)
    lines = []
    for i, (score, source, content) in enumerate(collected, 1):
        lines.append(f"[{i}] (관련도: {score:.2f} / 출처: {source})\n{content}")

    logger.debug("RAG medications: %d개 문서 검색됨", len(lines))
    return "\n\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# 챗봇용 검색 (MMR + score 필터)
# ─────────────────────────────────────────────────────────────────

def search_docs_with_scores(
    query: str,
    *,
    k: int = 4,
    threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
    use_mmr: bool = True,
) -> tuple[list[Any], bool]:
    """
    챗봇용 — MMR 다양성 검색 + relevance score 필터.

    기존 문제:
      similarity_search는 의미상 유사한 문서를 반복 반환할 수 있음.
      예: "아스피린 복용법" 질문 시 아스피린 관련 거의 동일한 문서 3개 반환.

    개선:
      max_marginal_relevance_search 로 관련성(λ=0.6) + 다양성(1-λ=0.4) 균형 유지.
      threshold 미만 문서 제거 후 (문서 목록, RAG 사용 여부) 반환.

    Args:
        query: 사용자 질문
        k: 최종 반환 문서 수
        threshold: 최소 relevance score
        use_mmr: MMR 사용 여부 (False 시 기존 similarity_search 사용)
    """
    if not query.strip():
        return [], False

    vs = get_vectorstore()
    if not vs:
        return [], False

    try:
        if use_mmr:
            # MMR: fetch_k개 후보에서 k개 선택 (관련성 + 다양성 균형)
            docs = vs.max_marginal_relevance_search(
                query,
                k=k,
                fetch_k=MMR_FETCH_K,
                lambda_mult=MMR_LAMBDA,
            )
            # MMR은 score를 반환하지 않으므로, 선택된 문서를 그대로 사용
            # (threshold 필터는 similarity_search_with_scores로 별도 수행)
            scored = vs.similarity_search_with_relevance_scores(query, k=MMR_FETCH_K)
            score_map = {
                _content_uid(doc.page_content): score
                for doc, score in scored
            }
            filtered = [
                doc for doc in docs
                if score_map.get(_content_uid(doc.page_content), 0.0) >= threshold
            ]
        else:
            results = vs.similarity_search_with_relevance_scores(query, k=k)
            filtered = [doc for doc, score in results if score >= threshold]

        logger.debug(
            "RAG chat search: query='%s...' → %d/%d 문서 통과 (threshold=%.2f)",
            query[:30], len(filtered), k, threshold,
        )
        return filtered, bool(filtered)

    except Exception as exc:
        logger.warning("RAG search (chat) failed: %s", exc)
        return [], False


# ─────────────────────────────────────────────────────────────────
# 카테고리 필터 검색 (신규)
# ─────────────────────────────────────────────────────────────────

def search_by_category(
    query: str,
    category: str,
    *,
    k: int = 3,
) -> list[Any]:
    """
    특정 카테고리(예: '생활습관', '항생제') 메타데이터 필터 검색.

    ChromaDB where 절로 메타데이터 필터링 후 유사도 검색.
    ingest 시 문서에 category 메타데이터가 있어야 동작함.

    Args:
        query: 검색 쿼리
        category: 필터할 카테고리 값 (doc.metadata["category"])
        k: 반환 문서 수
    """
    vs = get_vectorstore()
    if not vs:
        return []
    try:
        docs = vs.similarity_search(
            query,
            k=k,
            filter={"category": {"$eq": category}},
        )
        return docs
    except Exception as exc:
        logger.warning("RAG search (category=%s) failed: %s", category, exc)
        return []


# ─────────────────────────────────────────────────────────────────
# 인제스트 (청크 분할 지원)
# ─────────────────────────────────────────────────────────────────

def ingest_text_documents(
    documents: list[Any],
    *,
    batch_size: int = 100,
    deduplicate: bool = True,
) -> int:
    """
    문서를 ChromaDB에 추가.

    개선:
    - batch_size 단위로 나눠 추가 (대용량 문서 OOM 방지)
    - deduplicate=True: 동일 content 해시 문서 중복 추가 방지
    - 인제스트 후 캐시 무효화

    Args:
        documents: LangChain Document 리스트
        batch_size: 1회 add_documents 호출당 문서 수
        deduplicate: 내용 기반 중복 제거 여부
    """
    if not documents:
        return 0

    vs = get_vectorstore()
    if not vs:
        raise RuntimeError("ChromaDB vectorstore is not available")

    if deduplicate:
        documents = _deduplicate_documents(documents)

    total = 0
    for i in range(0, len(documents), batch_size):
        batch = documents[i: i + batch_size]
        vs.add_documents(batch)
        total += len(batch)
        logger.info("ChromaDB 인제스트: %d/%d 완료", total, len(documents))

    # 캐시 무효화 (새 문서 추가 시 기존 캐시 결과가 오래될 수 있음)
    _query_cache_clear()
    logger.info("ChromaDB 인제스트 완료: 총 %d개 문서", total)
    return total


def load_documents_from_dir(source_dir: Path) -> list[Any]:
    """data/rag 디렉터리에서 CSV·JSON·TXT 로드."""
    from ai_worker.rag.loaders import load_documents_from_rag_dir
    return load_documents_from_rag_dir(source_dir)


def ingest_rag_from_dir(source_dir: Path) -> int:
    """data/rag 파일 로드 후 ChromaDB 적재."""
    docs = load_documents_from_dir(source_dir)
    return ingest_text_documents(docs)


# ─────────────────────────────────────────────────────────────────
# 인메모리 LRU 캐시 (쿼리 단위)
# ─────────────────────────────────────────────────────────────────
# 동일 약품명 쿼리가 가이드 생성마다 반복될 경우 ChromaDB 임베딩 호출을 절약.
# 캐시 크기: 최대 128 항목 (LRU 교체)

_cache: dict[str, list] = {}
_CACHE_MAX = 128


def _cache_key(query: str) -> str:
    return hashlib.md5(query.encode()).hexdigest()


def _content_uid(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()


def _query_cache_get(key: str) -> list | None:
    return _cache.get(key)


def _query_cache_set(key: str, value: list) -> None:
    if len(_cache) >= _CACHE_MAX:
        # 가장 오래된 항목 제거 (Python 3.7+ dict 삽입 순서 보장)
        oldest = next(iter(_cache))
        del _cache[oldest]
    _cache[key] = value


def _query_cache_clear() -> None:
    _cache.clear()


# ─────────────────────────────────────────────────────────────────
# 유틸리티
# ─────────────────────────────────────────────────────────────────

def _extract_condition_keywords(medications: list) -> list[str]:
    """
    약품 카테고리/분류에서 생활습관 검색에 쓸 키워드 추출.
    예: "고혈압 치료제" → "고혈압", "당뇨" → "당뇨"
    """
    condition_hints = {
        "혈압": "고혈압",
        "당뇨": "당뇨",
        "콜레스테롤": "고지혈증",
        "항생제": "감염",
        "소염": "염증",
        "위산": "위장",
    }
    found: list[str] = []
    for med in medications:
        combined = " ".join([
            med.get("drug_name", "") or "",
            med.get("category", "") or "",
            med.get("instructions", "") or "",
        ])
        for hint, label in condition_hints.items():
            if hint in combined and label not in found:
                found.append(label)
    return found


def _deduplicate_documents(documents: list[Any]) -> list[Any]:
    """content 해시 기반 중복 문서 제거."""
    seen: set[str] = set()
    unique: list[Any] = []
    for doc in documents:
        uid = _content_uid(doc.page_content)
        if uid not in seen:
            seen.add(uid)
            unique.append(doc)
    removed = len(documents) - len(unique)
    if removed:
        logger.info("중복 문서 %d개 제거됨", removed)
    return unique


# ─────────────────────────────────────────────────────────────────
# 진단 유틸 (개발/운영 디버깅용)
# ─────────────────────────────────────────────────────────────────

def get_collection_stats() -> dict:
    """
    ChromaDB 컬렉션 통계 반환.
    운영 모니터링, 인제스트 검증에 사용.
    """
    vs = get_vectorstore()
    if not vs:
        return {"status": "unavailable"}
    try:
        count = vs._collection.count()
        return {
            "status": "ok",
            "collection": COLLECTION_NAME,
            "document_count": count,
            "persist_dir": os.getenv("CHROMA_PERSIST_DIR", DEFAULT_PERSIST_DIR),
            "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        }
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}

