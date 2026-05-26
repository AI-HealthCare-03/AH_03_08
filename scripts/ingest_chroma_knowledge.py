"""data/rag (CSV·JSON·TXT) → ChromaDB 적재.

Usage:
  uv run python scripts/ingest_chroma_knowledge.py
  CHROMA_PERSIST_DIR=./chroma_data uv run python scripts/ingest_chroma_knowledge.py
"""

import os
from pathlib import Path

from ai_worker.rag.chroma_store import ingest_rag_from_dir

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "rag"


def main() -> None:
    source = Path(os.getenv("RAG_SOURCE_DIR", str(DEFAULT_SOURCE)))
    count = ingest_rag_from_dir(source)
    if count == 0:
        raise SystemExit(f"No documents (.csv/.json/.txt) in {source}")

    print(f"OK: ingested {count} document(s) from {source}")


if __name__ == "__main__":
    main()
