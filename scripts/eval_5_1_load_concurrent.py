"""5-1 부하 테스트 — 동시 요청 GET /users/me (실측).

Locust 없이 httpx + asyncio로 동시 사용자 수를 시뮬레이션한다.
각 시나리오: virtual_users 명이 각각 requests_per_user 회 호출.

Usage:
  $env:EVAL_EMAIL="jimin_medilog@example.com"
  $env:EVAL_PASSWORD="Password123!"
  uv run python scripts/eval_5_1_load_concurrent.py
  uv run python scripts/eval_5_1_load_concurrent.py --output docs/evaluation/reports/5-1-load-report.md
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_guide_common import BASE_URL, login_client  # noqa: E402

P95_LIMIT_MS = 3000
DEFAULT_SCENARIOS = [(1, 100), (10, 100), (50, 100), (100, 100)]


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    qs = statistics.quantiles(values, n=100, method="inclusive")
    idx = max(0, min(99, int(p) - 1))
    return qs[idx]


def _stats(samples: list[float]) -> dict:
    if not samples:
        return {"count": 0, "p50_ms": 0, "p95_ms": 0, "p99_ms": 0, "max_ms": 0, "errors": 0}
    return {
        "count": len(samples),
        "p50_ms": round(_percentile(samples, 50), 1),
        "p95_ms": round(_percentile(samples, 95), 1),
        "p99_ms": round(_percentile(samples, 99), 1),
        "max_ms": round(max(samples), 1),
        "errors": 0,
    }


async def _virtual_user(
    user_idx: int,
    headers: dict[str, str],
    requests_per_user: int,
    samples: list[float],
    errors: list[int],
) -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        for _ in range(requests_per_user):
            t0 = time.perf_counter()
            try:
                r = await client.get("/users/me", headers=headers)
                ms = (time.perf_counter() - t0) * 1000
                if r.status_code == 200:
                    samples.append(ms)
                else:
                    errors.append(r.status_code)
            except Exception:
                errors.append(-1)


async def _run_scenario(
    virtual_users: int,
    requests_per_user: int,
    headers: dict[str, str],
) -> dict:
    samples: list[float] = []
    errors: list[int] = []
    t0 = time.perf_counter()
    await asyncio.gather(*[_virtual_user(i, headers, requests_per_user, samples, errors) for i in range(virtual_users)])
    elapsed = time.perf_counter() - t0
    st = _stats(samples)
    st["errors"] = len(errors)
    st["virtual_users"] = virtual_users
    st["requests_per_user"] = requests_per_user
    st["total_requests"] = virtual_users * requests_per_user
    st["elapsed_sec"] = round(elapsed, 2)
    st["pass"] = st["p95_ms"] <= P95_LIMIT_MS and len(errors) == 0
    return st


def _md(results: list[dict], executed_at: str) -> str:
    lines = [
        "# MediLog 8조 — 5-1 부하 테스트 실측 보고서",
        "",
        "## 1. 개요",
        "",
        "| 항목 | 내용 |",
        "|------|------|",
        "| 평가 항목 | 5-1 P95 Latency (부하) |",
        "| 대상 API | `GET /api/v1/users/me` |",
        f"| 실행 일시 (UTC) | {executed_at} |",
        "| 도구 | httpx + asyncio (동시 사용자 시뮬레이션) |",
        "| 기준 | P95 ≤ 3,000ms |",
        "",
        "## 2. 결과표",
        "",
        "| 동시 사용자 | 요청/인 | p50 (ms) | p95 (ms) | p99 (ms) | max (ms) | 오류 | 판정 |",
        "|-------------|---------|----------|----------|----------|----------|------|------|",
    ]
    for r in results:
        verdict = "PASS" if r["pass"] else "FAIL"
        lines.append(
            f"| {r['virtual_users']} | {r['requests_per_user']} | {r['p50_ms']} | "
            f"**{r['p95_ms']}** | {r['p99_ms']} | {r['max_ms']} | {r['errors']} | {verdict} |"
        )
    lines.extend(
        [
            "",
            "## 3. 결론",
            "",
            f"- 총 {len(results)}개 시나리오 중 "
            f"{sum(1 for r in results if r['pass'])}/{len(results)} PASS (P95 ≤ {P95_LIMIT_MS}ms).",
            "- 수치는 로컬 Docker(fastapi+mysql+redis) 실측값이다.",
            "",
        ]
    )
    return "\n".join(lines)


async def main_async(args: argparse.Namespace) -> int:
    executed_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    client, headers = await login_client()
    await client.aclose()

    scenarios = DEFAULT_SCENARIOS
    if args.quick:
        scenarios = [(1, 20), (10, 20)]

    results: list[dict] = []
    for users, per_user in scenarios:
        print(f"scenario: {users} users x {per_user} requests ...", flush=True)
        r = await _run_scenario(users, per_user, headers)
        results.append(r)
        print(f"  p95={r['p95_ms']}ms pass={r['pass']}", flush=True)

    out_md = Path(args.output)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(_md(results, executed_at), encoding="utf-8")

    out_json = out_md.with_suffix(".json")
    out_json.write_text(
        json.dumps({"executed_at": executed_at, "scenarios": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {out_md}")
    print(f"wrote {out_json}")
    return 0 if all(r["pass"] for r in results) else 1


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="docs/evaluation/reports/5-1-load-report.md")
    p.add_argument("--quick", action="store_true", help="1/10 users x 20 requests only")
    raise SystemExit(asyncio.run(main_async(p.parse_args())))


if __name__ == "__main__":
    main()
