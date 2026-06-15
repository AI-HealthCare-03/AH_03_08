"""
비동기 처리 성능 벤치마크 (3-2)

동일 LLM 호출을 순차(sequential) vs 동시(concurrent, asyncio.gather)로
N건 실행해 총 소요시간과 평균 latency를 비교한다.

실행: uv run python scripts/eval/async_benchmark.py [--n 5]
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv(Path(__file__).parents[2] / "envs" / ".local.env")
sys.path.insert(0, str(Path(__file__).parents[2]))

from ai_worker.prompts.llm_prompts import build_chat_system_prompt  # noqa: E402

TESTCASES_PATH = Path(__file__).parent / "chatbot" / "testcases.json"
RESULTS_DIR = Path(__file__).parent / "chatbot" / "results"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _llm() -> ChatOpenAI:
    return ChatOpenAI(model=MODEL, temperature=0, max_tokens=256, api_key=os.getenv("OPENAI_API_KEY", ""))


def _build_messages(case: dict) -> list:
    system_prompt = build_chat_system_prompt(
        user_health={},
        rag_docs=[],
        current_record={"disease_code": case["expected_kcd_code"]},
        disease_name=case["expected_name"],
    )
    return [SystemMessage(content=system_prompt), HumanMessage(content=case["question"])]


async def _run_sequential(all_msgs: list, llm: ChatOpenAI) -> tuple[float, list[float]]:
    latencies: list[float] = []
    t_start = time.perf_counter()
    for msgs in all_msgs:
        t0 = time.perf_counter()
        await llm.ainvoke(msgs)
        latencies.append(time.perf_counter() - t0)
    return time.perf_counter() - t_start, latencies


async def _call_one(msgs: list, llm: ChatOpenAI) -> float:
    t0 = time.perf_counter()
    await llm.ainvoke(msgs)
    return time.perf_counter() - t0


async def _run_concurrent(all_msgs: list, llm: ChatOpenAI) -> tuple[float, list[float]]:
    t_start = time.perf_counter()
    latencies = await asyncio.gather(*[_call_one(msgs, llm) for msgs in all_msgs])
    return time.perf_counter() - t_start, list(latencies)


async def main() -> None:
    parser = argparse.ArgumentParser(description="순차 vs 동시 LLM 호출 벤치마크")
    parser.add_argument("--n", type=int, default=5, help="요청 수 (기본: 5)")
    args = parser.parse_args()

    testcases = json.loads(TESTCASES_PATH.read_text(encoding="utf-8"))[: args.n]
    llm = _llm()

    print(f"[async_benchmark] 모델: {MODEL}, 요청 수: {len(testcases)}개\n")

    # 타이밍 외부에서 메시지 미리 생성 (kcd_lookup 등 전처리 시간 제외)
    print("  메시지 준비 중 ...", flush=True)
    all_msgs = [_build_messages(c) for c in testcases]

    print("  [1/2] 순차 실행 (sequential) ...", flush=True)
    seq_total, seq_latencies = await _run_sequential(all_msgs, llm)
    print(f"        완료: {seq_total:.2f}s")

    print("  [2/2] 동시 실행 (concurrent) ...", flush=True)
    con_total, con_latencies = await _run_concurrent(all_msgs, llm)
    print(f"        완료: {con_total:.2f}s")

    speedup = seq_total / con_total if con_total > 0 else 0.0
    seq_avg = sum(seq_latencies) / len(seq_latencies)
    con_avg = sum(con_latencies) / len(con_latencies)

    print(f"\n{'=' * 56}")
    print(f"  {'':22} {'순차(sequential)':>14} {'동시(concurrent)':>14}")
    print(f"  {'-' * 52}")
    print(f"  {'총 소요시간 (s)':<22} {seq_total:>14.2f} {con_total:>14.2f}")
    print(f"  {'평균 latency (s)':<22} {seq_avg:>14.2f} {con_avg:>14.2f}")
    print(f"  {'최대 latency (s)':<22} {max(seq_latencies):>14.2f} {max(con_latencies):>14.2f}")
    print(f"  {'최소 latency (s)':<22} {min(seq_latencies):>14.2f} {min(con_latencies):>14.2f}")
    print(f"  {'-' * 52}")
    print(f"  속도 향상 (speedup): {speedup:.2f}x  "
          f"({(1 - con_total / seq_total) * 100:.1f}% 단축)")
    print(f"{'=' * 56}")

    output = {
        "eval_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": MODEL,
        "n_requests": len(testcases),
        "sequential": {
            "total_sec": round(seq_total, 3),
            "avg_latency_sec": round(seq_avg, 3),
            "max_latency_sec": round(max(seq_latencies), 3),
            "min_latency_sec": round(min(seq_latencies), 3),
            "latencies_sec": [round(lat, 3) for lat in seq_latencies],
        },
        "concurrent": {
            "total_sec": round(con_total, 3),
            "avg_latency_sec": round(con_avg, 3),
            "max_latency_sec": round(max(con_latencies), 3),
            "min_latency_sec": round(min(con_latencies), 3),
            "latencies_sec": [round(lat, 3) for lat in con_latencies],
        },
        "speedup": round(speedup, 2),
        "time_saved_pct": round((1 - con_total / seq_total) * 100, 1) if seq_total > 0 else 0.0,
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    filename = RESULTS_DIR / f"async_benchmark_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    filename.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n결과 저장: {filename}")


if __name__ == "__main__":
    asyncio.run(main())
