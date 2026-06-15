"""
챗봇 KCD 검증 평가 스크립트

실행: uv run python scripts/eval/chatbot/run_eval.py [--split all|train|test]
결과: scripts/eval/chatbot/results/YYYY-MM-DD_HHMMSS.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv(Path(__file__).parents[3] / "envs" / ".local.env")

sys.path.insert(0, str(Path(__file__).parents[3]))

from ai_worker.kcd import synonyms as kcd_synonyms  # noqa: E402
from ai_worker.prompts.llm_prompts import build_chat_system_prompt  # noqa: E402

TESTCASES_PATH = Path(__file__).parent / "testcases.json"
RESULTS_DIR = Path(__file__).parent / "results"

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _llm() -> ChatOpenAI:
    return ChatOpenAI(model=MODEL, temperature=0, max_tokens=512, api_key=os.getenv("OPENAI_API_KEY", ""))


def _run_case(case: dict, llm: ChatOpenAI) -> dict:
    question = case["question"]
    expected_code = case["expected_kcd_code"]
    expected_name = case["expected_name"]

    # 실제 앱과 동일하게 disease_code를 current_record로 주입
    system_prompt = build_chat_system_prompt(
        user_health={},
        rag_docs=[],
        current_record={"disease_code": expected_code},
        disease_name=expected_name,
    )
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=question)])
    answer = response.content

    exact_name_matched = expected_name in answer
    all_names = kcd_synonyms(expected_code) or [expected_name]
    name_matched = any(name in answer for name in all_names)

    return {
        "id": case["id"],
        "category": case.get("category", ""),
        "split": case.get("split", "train"),
        "question": question,
        "expected_kcd_code": expected_code,
        "expected_name": expected_name,
        "exact_name_matched": exact_name_matched,
        "name_matched": name_matched,
        "llm_answer": answer,
        "passed": name_matched,
    }


def _calc_metrics(results: list[dict]) -> dict:
    total = len(results)
    exact_match = sum(1 for r in results if r["exact_name_matched"])
    synonym_match = sum(1 for r in results if r["name_matched"])

    return {
        "total": total,
        "passed": synonym_match,
        "failed": total - synonym_match,
        "name_accuracy": round(exact_match / total, 4),       # 정확 명칭 일치율
        "synonym_accuracy": round(synonym_match / total, 4),  # 동의어 포함 일치율
    }


def main():
    parser = argparse.ArgumentParser(description="챗봇 KCD 검증 평가")
    parser.add_argument(
        "--split",
        choices=["all", "train", "test"],
        default="all",
        help="평가할 데이터 분할 (기본: all)",
    )
    args = parser.parse_args()

    all_cases = json.loads(TESTCASES_PATH.read_text(encoding="utf-8"))
    testcases = all_cases if args.split == "all" else [c for c in all_cases if c.get("split") == args.split]

    llm = _llm()
    print(f"[eval] 모델: {MODEL}, split={args.split}, 테스트 케이스: {len(testcases)}개\n")

    results = []
    for i, case in enumerate(testcases, 1):
        print(f"  [{i:02d}/{len(testcases)}] {case['id']} ... ", end="", flush=True)
        result = _run_case(case, llm)
        results.append(result)
        status = "PASS" if result["passed"] else f"FAIL (exact={result['exact_name_matched']}, synonym={result['name_matched']})"
        print(status)

    metrics = _calc_metrics(results)

    output = {
        "eval_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": MODEL,
        "split": args.split,
        "total_cases": len(results),
        "metrics": metrics,
        "cases": results,
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    filename = RESULTS_DIR / f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    filename.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'=' * 50}")
    print(f"  Split           : {args.split}  ({len(results)}건)")
    print(f"  정확 명칭 일치율 : {metrics['name_accuracy']:.4f}")
    print(f"  동의어 포함 일치율: {metrics['synonym_accuracy']:.4f}")
    print(f"  통과 / 전체      : {metrics['passed']} / {metrics['total']}")
    print(f"{'=' * 50}")
    print(f"\n결과 저장: {filename}")


if __name__ == "__main__":
    main()
