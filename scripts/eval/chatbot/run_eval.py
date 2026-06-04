"""
챗봇 KCD 검증 평가 스크립트

실행: uv run python scripts/eval/chatbot/run_eval.py
결과: scripts/eval/chatbot/results/YYYY-MM-DD_HHMMSS.json
"""

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

from ai_worker.kcd import lookup as kcd_lookup, synonyms as kcd_synonyms
from ai_worker.prompts.llm_prompts import build_chat_system_prompt

TESTCASES_PATH = Path(__file__).parent / "testcases.json"
RESULTS_DIR = Path(__file__).parent / "results"

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _llm() -> ChatOpenAI:
    return ChatOpenAI(model=MODEL, temperature=0, max_tokens=512, api_key=os.getenv("OPENAI_API_KEY", ""))


def _run_case(case: dict, llm: ChatOpenAI) -> dict:
    question = case["question"]
    expected_code = case["expected_kcd_code"]
    expected_name = case["expected_name"]

    kcd_facts = kcd_lookup(question)
    code_detected = expected_code in kcd_facts

    system_prompt = build_chat_system_prompt(user_health={}, rag_docs=[], kcd_facts=kcd_facts)
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=question)])
    answer = response.content

    # KCD 동의어 중 하나라도 답변에 포함되면 통과
    all_names = kcd_synonyms(expected_code) or [expected_name]
    name_matched = any(name in answer for name in all_names)

    return {
        "id": case["id"],
        "category": case.get("category", ""),
        "question": question,
        "expected_kcd_code": expected_code,
        "expected_name": expected_name,
        "code_detected": code_detected,
        "name_matched": name_matched,
        "llm_answer": answer,
        "passed": code_detected and name_matched,
    }


def _calc_f1(results: list[dict]) -> dict:
    tp = sum(1 for r in results if r["code_detected"] and r["name_matched"])
    fp = sum(1 for r in results if r["code_detected"] and not r["name_matched"])
    fn = sum(1 for r in results if not r["code_detected"])

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "code_detection_rate": round(sum(1 for r in results if r["code_detected"]) / len(results), 4),
        "name_accuracy": round(sum(1 for r in results if r["name_matched"]) / len(results), 4),
    }


def main():
    testcases = json.loads(TESTCASES_PATH.read_text(encoding="utf-8"))
    llm = _llm()
    print(f"[eval] 모델: {MODEL}, 테스트 케이스: {len(testcases)}개\n")

    results = []
    for i, case in enumerate(testcases, 1):
        print(f"  [{i:02d}/{len(testcases)}] {case['id']} ... ", end="", flush=True)
        result = _run_case(case, llm)
        results.append(result)
        status = "PASS" if result["passed"] else f"FAIL (감지={result['code_detected']}, 명칭={result['name_matched']})"
        print(status)

    metrics = _calc_f1(results)

    output = {
        "eval_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": MODEL,
        "total_cases": len(results),
        "metrics": metrics,
        "cases": results,
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    filename = RESULTS_DIR / f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    filename.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*50}")
    print(f"  F1 Score     : {metrics['f1_score']:.4f}")
    print(f"  Precision    : {metrics['precision']:.4f}")
    print(f"  Recall       : {metrics['recall']:.4f}")
    print(f"  코드 감지율  : {metrics['code_detection_rate']:.4f}")
    print(f"  명칭 정확도  : {metrics['name_accuracy']:.4f}")
    print(f"{'='*50}")
    print(f"\n결과 저장: {filename}")


if __name__ == "__main__":
    main()
