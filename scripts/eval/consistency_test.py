"""
동일 입력 결과 일관성 검증 (3-3)

동일 케이스를 K회 반복 실행해 pass rate 분산·표준편차를 측정한다.
temperature=0 설정이 결과 일관성에 미치는 효과를 수치로 증명한다.

실행: uv run python scripts/eval/consistency_test.py [--runs 5] [--cases 5]
"""

import argparse
import json
import os
import statistics
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv(Path(__file__).parents[2] / "envs" / ".local.env")
sys.path.insert(0, str(Path(__file__).parents[2]))

from ai_worker.kcd import synonyms as kcd_synonyms  # noqa: E402
from ai_worker.prompts.llm_prompts import build_chat_system_prompt  # noqa: E402

TESTCASES_PATH = Path(__file__).parent / "chatbot" / "testcases.json"
RESULTS_DIR = Path(__file__).parent / "chatbot" / "results"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _llm() -> ChatOpenAI:
    return ChatOpenAI(model=MODEL, temperature=0, max_tokens=512, api_key=os.getenv("OPENAI_API_KEY", ""))


def _run_once(case: dict, llm: ChatOpenAI) -> bool:
    system_prompt = build_chat_system_prompt(
        user_health={},
        rag_docs=[],
        current_record={"disease_code": case["expected_kcd_code"]},
        disease_name=case["expected_name"],
    )
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=case["question"])])
    all_names = kcd_synonyms(case["expected_kcd_code"]) or [case["expected_name"]]
    return any(name in response.content for name in all_names)


def main():
    parser = argparse.ArgumentParser(description="동일 입력 일관성 테스트")
    parser.add_argument("--runs", type=int, default=30, help="케이스당 반복 횟수 (기본: 30)")
    parser.add_argument("--cases", type=int, default=None, help="테스트할 케이스 수 (기본: 전체)")
    args = parser.parse_args()

    all_cases = json.loads(TESTCASES_PATH.read_text(encoding="utf-8"))
    testcases = all_cases if args.cases is None else all_cases[: args.cases]
    llm = _llm()

    print(f"[consistency] 모델: {MODEL}, temperature=0, 케이스: {len(testcases)}/{len(all_cases)}개, 반복: {args.runs}회\n")

    case_results: list[dict] = []
    for case in testcases:
        passes: list[int] = []
        for run_idx in range(args.runs):
            print(f"  {case['id']} ({run_idx + 1}/{args.runs}) ... ", end="", flush=True)
            passed = _run_once(case, llm)
            passes.append(int(passed))
            print("PASS" if passed else "FAIL")

        pass_rate = sum(passes) / len(passes)
        std_dev = statistics.stdev(passes) if len(passes) > 1 else 0.0
        case_results.append(
            {
                "id": case["id"],
                "category": case.get("category", ""),
                "pass_rate": round(pass_rate, 4),
                "std_dev": round(std_dev, 4),
                "runs": passes,
                "consistent": std_dev == 0.0,
            }
        )

    consistent_count = sum(1 for r in case_results if r["consistent"])
    avg_pass_rate = sum(r["pass_rate"] for r in case_results) / len(case_results)
    avg_std_dev = sum(r["std_dev"] for r in case_results) / len(case_results)

    print(f"\n{'=' * 62}")
    print(f"  {'케이스':<12} {'카테고리':<18} {'pass_rate':>10} {'std_dev':>8} {'일관성':>6}")
    print(f"  {'-' * 57}")
    for r in case_results:
        flag = "O" if r["consistent"] else "X"
        print(
            f"  {r['id']:<12} {r['category']:<18} "
            f"{r['pass_rate']:>10.4f} {r['std_dev']:>8.4f} {flag:>6}"
        )
    print(f"  {'-' * 57}")
    print(f"  {'평균':<30} {avg_pass_rate:>10.4f} {avg_std_dev:>8.4f}")
    print(f"\n  완전 일관 케이스: {consistent_count}/{len(case_results)}  "
          f"({consistent_count / len(case_results):.0%})")
    print(f"{'=' * 62}")

    output = {
        "eval_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": MODEL,
        "temperature": 0.0,
        "runs_per_case": args.runs,
        "total_cases": len(case_results),
        "avg_pass_rate": round(avg_pass_rate, 4),
        "avg_std_dev": round(avg_std_dev, 4),
        "consistent_ratio": round(consistent_count / len(case_results), 4),
        "cases": case_results,
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    filename = RESULTS_DIR / f"consistency_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    filename.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n결과 저장: {filename}")


if __name__ == "__main__":
    main()
