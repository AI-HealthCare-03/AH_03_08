"""
개선된 ChromaDB 인제스트 스크립트

Usage:
  uv run python scripts/ingest_chroma_knowledge.py
  uv run python scripts/ingest_chroma_knowledge.py --dry-run   # 실제 적재 없이 문서 수만 확인
  uv run python scripts/ingest_chroma_knowledge.py --stats     # 현재 컬렉션 통계만 출력
  uv run python scripts/ingest_chroma_knowledge.py --reset     # 컬렉션 초기화 후 재적재
  CHROMA_PERSIST_DIR=./chroma_data uv run python scripts/ingest_chroma_knowledge.py
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "rag"

sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:  # noqa: C901
    parser = argparse.ArgumentParser(description="ChromaDB RAG 인제스트")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="RAG 소스 디렉터리")
    parser.add_argument("--dry-run", action="store_true", help="문서 파싱만 확인 (적재 없음)")
    parser.add_argument("--stats", action="store_true", help="현재 컬렉션 통계 출력 후 종료")
    parser.add_argument("--reset", action="store_true", help="컬렉션 초기화 후 재적재")
    args = parser.parse_args()

    from ai_worker.rag.chroma_store import (
        get_collection_stats,
        get_vectorstore,
        ingest_text_documents,
        load_documents_from_dir,
    )

    # --stats: 현재 상태만 출력
    if args.stats:
        stats = get_collection_stats()
        print("\n=== ChromaDB 컬렉션 통계 ===")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        return

    source = Path(args.source)
    if not source.is_dir():
        raise SystemExit(f"소스 디렉터리 없음: {source}")

    # 문서 로드 (파싱만)
    docs = load_documents_from_dir(source)
    if not docs:
        raise SystemExit(f"로드된 문서 없음: {source}")

    # 카테고리 분포 출력
    categories = Counter(d.metadata.get("category", "기타") for d in docs)
    print("\n=== RAG 문서 로드 결과 ===")
    print(f"  총 문서 수: {len(docs)}")
    print("  카테고리 분포:")
    for cat, cnt in categories.most_common():
        print(f"    {cat}: {cnt}개")

    # 샘플 출력 (처음 3개)
    print("\n  샘플 (처음 3개):")
    for i, doc in enumerate(docs[:3], 1):
        preview = doc.page_content[:80].replace("\n", " ")
        print(f"    [{i}] [{doc.metadata.get('category')}] {preview}...")

    if args.dry_run:
        print("\n--dry-run: 실제 적재 건너뜀")
        return

    # --reset: 컬렉션 초기화
    if args.reset:
        vs = get_vectorstore()
        if vs:
            try:
                vs._client.delete_collection(vs._collection.name)
                print("\n컬렉션 초기화 완료")
                # 싱글톤 재초기화
                get_vectorstore(force_reinit=True)
            except Exception as e:
                print(f"컬렉션 초기화 실패: {e}")

    # 적재
    count = ingest_text_documents(docs)
    print(f"\nOK: {count}개 문서 ChromaDB 적재 완료")

    # 적재 후 통계
    stats = get_collection_stats()
    print(f"  컬렉션 총 문서 수: {stats.get('document_count', '?')}")


if __name__ == "__main__":
    main()
