"""
평가 결과 히스토리 출력

실행: uv run python scripts/eval/show_history.py
"""

import json
from pathlib import Path

BASE = Path(__file__).parent


def _load_results(results_dir: Path) -> list[dict]:
    files = sorted(results_dir.glob("*.json"))
    rows = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            rows.append({"file": f.name, **data})
        except Exception:
            continue
    return rows


def _print_chatbot(rows: list[dict]):
    print("\n[챗봇 KCD 검증 히스토리]")
    print(f"{'날짜':<22} {'모델':<15} {'F1':>6} {'Precision':>10} {'Recall':>8} {'코드감지':>8} {'명칭정확':>8}")
    print("-" * 85)
    for r in rows:
        m = r.get("metrics", {})
        print(
            f"{r.get('eval_date', r['file']):<22} "
            f"{r.get('model', '-'):<15} "
            f"{m.get('f1_score', 0):>6.4f} "
            f"{m.get('precision', 0):>10.4f} "
            f"{m.get('recall', 0):>8.4f} "
            f"{m.get('code_detection_rate', 0):>8.4f} "
            f"{m.get('name_accuracy', 0):>8.4f}"
        )


def _print_ocr(rows: list[dict]):
    print("\n[OCR 정확도 히스토리]")
    print(f"{'날짜':<22} {'케이스':>6} {'필드정확도':>10} {'약물정확도':>10} {'종합':>8}")
    print("-" * 65)
    for r in rows:
        m = r.get("metrics", {})
        print(
            f"{r.get('eval_date', r['file']):<22} "
            f"{m.get('evaluated', 0):>6} "
            f"{m.get('avg_field_accuracy', 0):>10.4f} "
            f"{m.get('avg_medication_accuracy', 0):>10.4f} "
            f"{m.get('avg_overall', 0):>8.4f}"
        )


def main():
    chatbot_rows = _load_results(BASE / "chatbot" / "results")
    ocr_rows = _load_results(BASE / "ocr" / "results")

    if chatbot_rows:
        _print_chatbot(chatbot_rows)
    else:
        print("\n[챗봇] 결과 없음. run_eval.py 먼저 실행하세요.")

    if ocr_rows:
        _print_ocr(ocr_rows)
    else:
        print("\n[OCR] 결과 없음. run_eval.py 먼저 실행하세요.")


if __name__ == "__main__":
    main()
