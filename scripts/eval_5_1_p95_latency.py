"""5-1 P95 Latency — 조회(GET) API 응답시간 측정 (llm-worker 불필요).

Usage:
  $env:EVAL_EMAIL="your@email.com"
  $env:EVAL_PASSWORD="Password123!"
  uv run python scripts/eval_5_1_p95_latency.py
  uv run python scripts/eval_5_1_p95_latency.py --iterations 30 --output docs/evaluation/reports/5-1-report.md

기준: NREQ-PERF-001 — P95 ≤ 3,000ms
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_guide_common import BASE_URL, login_client

P95_LIMIT_MS = 3000
DEFAULT_ITERATIONS = 30


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    qs = statistics.quantiles(values, n=100, method="inclusive")
    idx = max(0, min(99, int(p) - 1))
    return qs[idx]


def _stats(samples: list[float]) -> dict[str, float]:
    if not samples:
        return {"count": 0, "min_ms": 0, "max_ms": 0, "avg_ms": 0, "p50_ms": 0, "p95_ms": 0}
    return {
        "count": len(samples),
        "min_ms": min(samples),
        "max_ms": max(samples),
        "avg_ms": statistics.mean(samples),
        "p50_ms": _percentile(samples, 50),
        "p95_ms": _percentile(samples, 95),
    }


async def _timed_get(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    path: str,
    *,
    params: dict | None = None,
) -> tuple[float, int]:
    t0 = time.perf_counter()
    r = await client.get(path, headers=headers, params=params)
    ms = (time.perf_counter() - t0) * 1000
    return ms, r.status_code


async def _discover_ids(client: httpx.AsyncClient, headers: dict[str, str]) -> dict[str, str | None]:
    guide_id = record_id = None
    r = await client.get("/guides", headers=headers, params={"page": 1, "limit": 1})
    if r.status_code == 200:
        data = r.json().get("data") or {}
        items = data.get("items") or data if isinstance(data, list) else []
        if isinstance(data, dict) and data.get("items"):
            items = data["items"]
        if items:
            guide_id = str(items[0].get("id") or items[0].get("guide_id") or "")
    r2 = await client.get("/records", headers=headers, params={"page": 1, "limit": 1})
    if r2.status_code == 200:
        body = r2.json()
        items = (body.get("data") or {}).get("items") or body.get("items") or []
        if items:
            record_id = str(items[0].get("id") or "")
    return {"guide_id": guide_id or None, "record_id": record_id or None}


def _build_targets(ids: dict[str, str | None]) -> list[dict[str, Any]]:
    today = date.today()
    targets: list[dict[str, Any]] = [
        {"name": "GET /users/me", "path": "/users/me"},
        {"name": "GET /users/me/allergies", "path": "/users/me/allergies"},
        {"name": "GET /users/me/conditions", "path": "/users/me/conditions"},
        {"name": "GET /guides", "path": "/guides", "params": {"page": 1, "limit": 10}},
        {"name": "GET /guides/feedbacks/list", "path": "/guides/feedbacks/list"},
        {"name": "GET /records", "path": "/records", "params": {"page": 1, "limit": 10}},
        {"name": "GET /notifications", "path": "/notifications"},
        {
            "name": "GET /calendars (월별)",
            "path": "/calendars",
            "params": {"year": str(today.year), "month": str(today.month)},
        },
        {
            "name": "GET /calendars/{date} (일별)",
            "path": f"/calendars/{today.isoformat()}",
        },
    ]
    if ids.get("guide_id"):
        gid = ids["guide_id"]
        targets.append({"name": "GET /guides/{id}", "path": f"/guides/{gid}"})
        targets.append({"name": "GET /guides/{id}/status", "path": f"/guides/{gid}/status"})
    if ids.get("record_id"):
        rid = ids["record_id"]
        targets.append({"name": "GET /records/{id}", "path": f"/records/{rid}"})
    return targets


def _to_markdown(report: dict) -> str:
    lines = [
        "# MediLog 8조 — 5-1 P95 Latency 측정 보고서",
        "",
        "## 1. 테스트 개요",
        "",
        "| 항목 | 내용 |",
        "|------|------|",
        "| 평가 항목 | 5-1 API P95 Latency (NREQ-PERF-001) |",
        f"| 기준 | P95 ≤ **{report['p95_limit_ms']:,}ms** |",
        f"| 실행 일시 (UTC) | {report['executed_at']} |",
        f"| API Base | `{report['api_base']}` |",
        f"| 반복 횟수 | 엔드포인트당 **{report['iterations']}회** |",
        "| 측정 범위 | **조회(GET) API만** (LLM generate 제외) |",
        "| 비고 | 3-2/3-3은 llm-worker 이슈로 중단, 5-1만 진행 |",
        "",
        "## 2. 결과표",
        "",
        "| API | p50 (ms) | **p95 (ms)** | max (ms) | 판정 |",
        "|-----|----------|--------------|----------|------|",
    ]
    pass_count = 0
    for row in report["endpoints"]:
        ok = row["p95_ms"] <= report["p95_limit_ms"] and row.get("errors", 0) == 0
        if ok:
            pass_count += 1
        verdict = "PASS" if ok else "FAIL"
        err = f" ({row['errors']} err)" if row.get("errors") else ""
        lines.append(
            f"| {row['name']} | {row['p50_ms']:.0f} | **{row['p95_ms']:.0f}** | {row['max_ms']:.0f} | {verdict}{err} |"
        )
    total = len(report["endpoints"])
    lines.extend(
        [
            "",
            f"**PASS:** {pass_count}/{total}",
            "",
            "## 3. 상세 (엔드포인트별)",
            "",
        ]
    )
    for row in report["endpoints"]:
        lines.append(f"### {row['name']}")
        lines.append("")
        lines.append(
            f"- samples: {row['count']}, min {row['min_ms']:.0f}ms, avg {row['avg_ms']:.0f}ms, "
            f"p50 {row['p50_ms']:.0f}ms, p95 {row['p95_ms']:.0f}ms, max {row['max_ms']:.0f}ms"
        )
        if row.get("errors"):
            lines.append(f"- HTTP errors: {row['errors']}")
        lines.append("")

    lines.extend(
        [
            "## 4. 결론",
            "",
            report["conclusion"],
            "",
            "## Notion 붙여넣기용 한 줄",
            "",
            report["one_liner"],
        ]
    )
    return "\n".join(lines)


async def main(iterations: int, output: Path | None) -> None:
    executed_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    client, headers = await login_client()
    try:
        ids = await _discover_ids(client, headers)
        targets = _build_targets(ids)
        endpoint_rows: list[dict] = []

        for target in targets:
            samples: list[float] = []
            errors = 0
            last_status = 0
            for _ in range(iterations):
                try:
                    ms, status = await _timed_get(
                        client,
                        headers,
                        target["path"],
                        params=target.get("params"),
                    )
                    last_status = status
                    if status >= 400:
                        errors += 1
                    else:
                        samples.append(ms)
                except Exception:
                    errors += 1
            st = _stats(samples)
            row = {
                "name": target["name"],
                "path": target["path"],
                "errors": errors,
                "last_status": last_status,
                **st,
            }
            endpoint_rows.append(row)
            mark = "PASS" if st["p95_ms"] <= P95_LIMIT_MS and errors == 0 else "FAIL"
            print(f"{target['name']}: p95={st['p95_ms']:.0f}ms [{mark}]")

        pass_n = sum(1 for r in endpoint_rows if r["p95_ms"] <= P95_LIMIT_MS and r["errors"] == 0)
        total = len(endpoint_rows)
        all_pass = pass_n == total
        conclusion = (
            f"조회(GET) API {total}개 엔드포인트를 각 {iterations}회 호출하였다. "
            f"P95 ≤ {P95_LIMIT_MS}ms 기준 **{pass_n}/{total} PASS**."
            + (
                " 전체 조회 API가 성능 기준을 만족한다."
                if all_pass
                else " 일부 엔드포인트가 기준을 초과하거나 오류가 있었다."
            )
            + " LLM 비동기(generate→done) 구간은 llm-worker 이슈로 본 측정에서 제외하였다."
        )
        one_liner = (
            f"5-1 P95(조회 API): {pass_n}/{total} PASS (기준 {P95_LIMIT_MS}ms). "
            "3-2/3-3는 llm-worker 미완료로 별도 이슈."
        )

        report = {
            "executed_at": executed_at,
            "api_base": BASE_URL,
            "iterations": iterations,
            "p95_limit_ms": P95_LIMIT_MS,
            "discovered_ids": ids,
            "endpoints": endpoint_rows,
            "conclusion": conclusion,
            "one_liner": one_liner,
        }

        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(_to_markdown(report), encoding="utf-8")
            print(f"\nReport: {output}")
    finally:
        await client.aclose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--output", type=Path, default=Path("docs/evaluation/reports/5-1-report.md"))
    args = parser.parse_args()
    asyncio.run(main(args.iterations, args.output))
