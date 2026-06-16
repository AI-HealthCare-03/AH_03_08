"""Post-deploy smoke test: login → generate guide → poll until done.

Usage:
  $env:EVAL_EMAIL="jimin_medilog@example.com"
  $env:EVAL_PASSWORD="Password123!"
  uv run python scripts/smoke_test_guide.py
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_guide_common import fetch_guide, login_client, poll_guide_done, setup_health_and_record  # noqa: E402


async def main() -> int:
    client, headers = await login_client()
    try:
        print("=== GUIDE SMOKE TEST ===")
        record_id = await setup_health_and_record(client, headers)
        print(f"[1] record_id={record_id}")

        t0 = time.perf_counter()
        r = await client.post("/guides/generate", headers=headers, json={"record_id": record_id})
        accept_ms = (time.perf_counter() - t0) * 1000
        r.raise_for_status()
        guide_id = r.json()["data"]["guide_id"]
        print(f"[2] POST /guides/generate: {r.status_code} ({accept_ms:.0f}ms) guide_id={guide_id}")

        status, polls = await poll_guide_done(client, headers, guide_id)
        total_s = time.perf_counter() - t0
        print(f"[3] status={status} polls={polls} total={total_s:.1f}s")

        guide = await fetch_guide(client, headers, guide_id)
        temp = guide.get("llm_temperature")
        print(f"[4] llm_temperature={temp} llm_model={guide.get('llm_model')}")

        ok = status == "done" and temp == 0.0
        print("=== RESULT:", "PASS" if ok else "FAIL", "===")
        return 0 if ok else 1
    finally:
        await client.aclose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
