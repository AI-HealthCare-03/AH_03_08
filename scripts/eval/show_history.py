"""
평가 결과 히스토리 출력

실행: uv run python scripts/eval/show_history.py
"""

import json
from pathlib import Path

BASE = Path(__file__).parent


_CHATBOT_PREFIXES = ("consistency_", "async_benchmark_")


def _load_results(results_dir: Path, exclude_prefixes: tuple = ()) -> list[dict]:
    files = sorted(results_dir.glob("*.json"))
    rows = []
    for f in files:
        if any(f.name.startswith(p) for p in exclude_prefixes):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            rows.append({"file": f.name, **data})
        except Exception:
            continue
    return rows


def _delta_str(current: float, prev: float | None) -> str:
    if prev is None:
        return "      -"
    diff = current - prev
    sign = "+" if diff >= 0 else ""
    return f"{sign}{diff:+.4f}"


def _primary_metric(m: dict) -> tuple[float, str]:
    """결과 포맷에 따라 주요 지표 값과 레이블을 반환한다."""
    if "synonym_accuracy" in m:
        return m["synonym_accuracy"], "syn_acc"
    return m.get("f1_score", 0), "f1    "


def _print_chatbot(rows: list[dict]):
    print("\n[챗봇 KCD 검증 히스토리]")
    print(f"{'날짜':<22} {'split':<6} {'모델':<15} {'주요지표':>8} {'Δ':>8} {'보조지표':>10}")
    print("-" * 78)
    prev_val: float | None = None
    for r in rows:
        m = r.get("metrics", {})
        val, label = _primary_metric(m)
        # 보조지표: 신규=name_accuracy, 구=precision
        sub = m.get("name_accuracy", 0) if "synonym_accuracy" in m else m.get("precision", 0)
        sub_label = "name_acc" if "synonym_accuracy" in m else "precision"
        split = r.get("split", "all")
        print(
            f"{r.get('eval_date', r['file']):<22} "
            f"{split:<6} "
            f"{r.get('model', '-'):<15} "
            f"{label}={val:.4f} "
            f"{_delta_str(val, prev_val):>8} "
            f"{sub_label}={sub:.4f}"
        )
        prev_val = val


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
    chatbot_rows = _load_results(BASE / "chatbot" / "results", exclude_prefixes=_CHATBOT_PREFIXES)
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
