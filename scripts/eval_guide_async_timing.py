"""3-2 비동기 처리 응답시간 측정 (202 수락 vs 완료까지).

Usage:
  uv run python scripts/eval_guide_async_timing.py
  uv run python scripts/eval_guide_async_timing.py --iterations 3 --output docs/evaluation/reports/3-2-report.md

측정:
  - accept_ms: POST /guides/generate → 202 응답 (비동기 즉시 반환)
  - total_ms: generate 요청 ~ status=done (동기 대기 시 사용자 체감 시간에 해당)
"""

import argparse
import asyncio
import json
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_guide_common import login_client, poll_guide_done, setup_health_and_record


def _avg(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def _to_markdown(report: dict) -> str:
    lines = [
        "# 3-2 가이드 생성 비동기 응답시간",
        "",
        f"- 실행 시각(UTC): {report['executed_at']}",
        f"- API: `{report['api_base']}`",
        f"- 측정 횟수: {report['iterations']}",
        "",
        "## 결과 (ms)",
        "",
        "| 구분 | 평균 | 최소 | 최대 | 설명 |",
        "|------|------|------|------|------|",
    ]
    for row in report["summary_rows"]:
        lines.append(
            f"| {row['name']} | {row['avg_ms']:.0f} | {row['min_ms']:.0f} | {row['max_ms']:.0f} | {row['note']} |"
        )
    lines.extend(
        [
            "",
            "## 비교 해석",
            "",
            report["interpretation"],
            "",
            "## Swagger 수동 측정 방법",
            "",
            "1. POST `/api/v1/guides/generate` — Network 탭 **Time** = accept_ms",
            "2. GET `/guides/{id}/status` 폴링 ~ `done` — 누적 시간 ≈ total_ms",
            "3. 동기(가정): 한 요청에서 LLM 완료까지 대기 → total_ms와 유사",
            "",
            "## Notion 붙여넣기용 결론",
            report["conclusion"],
        ]
    )
    return "\n".join(lines)


async def measure_once(client, headers, record_id: str) -> dict:
    t0 = time.perf_counter()
    r = await client.post("/guides/generate", headers=headers, json={"record_id": record_id})
    accept_ms = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    guide_id = r.json()["data"]["guide_id"]

    status, polls = await poll_guide_done(client, headers, guide_id)
    total_ms = (time.perf_counter() - t0) * 1000
    processing_ms = total_ms - accept_ms
    return {
        "guide_id": guide_id,
        "status": status,
        "accept_ms": round(accept_ms, 1),
        "total_ms": round(total_ms, 1),
        "processing_ms": round(processing_ms, 1),
        "polls": polls,
    }


async def main(iterations: int, output: Path | None) -> None:
    client, headers = await login_client()
    try:
        record_id = await setup_health_and_record(client, headers)
        rows: list[dict] = []
        for i in range(iterations):
            row = await measure_once(client, headers, record_id)
            if row["status"] != "done":
                raise SystemExit(f"iteration {i + 1} status={row['status']}")
            rows.append(row)
            print(f"iter {i + 1}:", row)

        accepts = [r["accept_ms"] for r in rows]
        totals = [r["total_ms"] for r in rows]
        processing = [r["processing_ms"] for r in rows]

        summary_rows = [
            {
                "name": "비동기 accept (202)",
                "avg_ms": _avg(accepts),
                "min_ms": min(accepts),
                "max_ms": max(accepts),
                "note": "API 즉시 반환",
            },
            {
                "name": "비동기 total (done까지)",
                "avg_ms": _avg(totals),
                "min_ms": min(totals),
                "max_ms": max(totals),
                "note": "폴링 포함 전체",
            },
            {
                "name": "백그라운드 처리",
                "avg_ms": _avg(processing),
                "min_ms": min(processing),
                "max_ms": max(processing),
                "note": "total − accept",
            },
            {
                "name": "동기 가정 (1요청 대기)",
                "avg_ms": _avg(totals),
                "min_ms": min(totals),
                "max_ms": max(totals),
                "note": "LLM 완료 후 응답 시나리오",
            },
        ]

        speedup = _avg(totals) / _avg(accepts) if _avg(accepts) else 0
        report = {
            "test": "3-2-async-timing",
            "executed_at": datetime.now(UTC).isoformat(),
            "api_base": str(client.base_url),
            "iterations": iterations,
            "measurements": rows,
            "summary_rows": summary_rows,
            "interpretation": (
                f"비동기 accept 평균 {_avg(accepts):.0f}ms vs 완료까지 평균 {_avg(totals):.0f}ms. "
                f"사용자는 약 {speedup:.1f}배 빠르게 '요청 접수' 응답을 받고, "
                "실제 LLM 처리는 Celery에서 백그라운드로 진행됩니다."
            ),
            "conclusion": (
                f"| 방식 | 평균 응답(ms) |\n|------|-------------|\n"
                f"| 비동기 (202 즉시) | {_avg(accepts):.0f} |\n"
                f"| 동기 가정 (완료까지) | {_avg(totals):.0f} |"
            ),
        }

        print(json.dumps(report, ensure_ascii=False, indent=2))
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(_to_markdown(report), encoding="utf-8")
            print(f"\nWrote {output}")
    finally:
        await client.aclose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    asyncio.run(main(args.iterations, args.output))
