"""
OCR 정확도 평가 스크립트

테스트 케이스 구조:
  scripts/eval/ocr/testcases/
    case_001/
      image.jpg   ← 처방전 이미지 (AI 생성 or 실제)
      label.json  ← 정답 라벨

label.json 형식:
  {
    "patient_name": "홍길동",
    "hospital": "서울내과의원",
    "disease_code": "N30.0",
    "medications": [
      {"name": "아목시실린", "dosage": 250.0, "frequency": 3, "days": 5}
    ]
  }

실행: uv run python scripts/eval/ocr/run_eval.py
결과: scripts/eval/ocr/results/YYYY-MM-DD_HHMMSS.json
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[3] / "envs" / ".local.env")

sys.path.insert(0, str(Path(__file__).parents[3]))

from ai_worker.core.config import Config
from ai_worker.ocr import get_ocr_provider
from ai_worker.tasks.ocr_task import _parse_with_openai

TESTCASES_DIR = Path(__file__).parent / "testcases"
RESULTS_DIR = Path(__file__).parent / "results"

SCALAR_FIELDS = ["patient_name", "hospital", "disease_code", "doctor", "pharmacy"]


def _similarity(a: str | None, b: str | None) -> float:
    if a is None and b is None:
        return 1.0
    if a is None or b is None:
        return 0.0
    return SequenceMatcher(None, a.strip(), b.strip()).ratio()


def _exact(a: str | None, b: str | None) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return a.strip().lower() == b.strip().lower()


def _score_medications(pred: list[dict], label: list[dict]) -> dict:
    if not label:
        return {"matched": 0, "total": 0, "accuracy": 1.0}

    matched = 0
    for lm in label:
        for pm in pred:
            if _similarity(pm.get("name"), lm.get("name")) >= 0.8:
                matched += 1
                break

    return {"matched": matched, "total": len(label), "accuracy": round(matched / len(label), 4)}


def _score_case(pred: dict, label: dict) -> dict:
    field_scores = {}
    for field in SCALAR_FIELDS:
        field_scores[field] = {
            "exact": _exact(pred.get(field), label.get(field)),
            "similarity": round(_similarity(pred.get(field), label.get(field)), 4),
            "predicted": pred.get(field),
            "expected": label.get(field),
        }

    med_score = _score_medications(pred.get("medications", []), label.get("medications", []))

    exact_fields = sum(1 for s in field_scores.values() if s["exact"])
    total_fields = len(SCALAR_FIELDS)
    field_accuracy = round(exact_fields / total_fields, 4)
    avg_similarity = round(sum(s["similarity"] for s in field_scores.values()) / total_fields, 4)

    return {
        "field_accuracy": field_accuracy,
        "avg_similarity": avg_similarity,
        "medication_accuracy": med_score["accuracy"],
        "overall": round((field_accuracy + med_score["accuracy"]) / 2, 4),
        "fields": field_scores,
        "medications": med_score,
    }


async def _run_case(case_dir: Path, config: Config) -> dict:
    label_path = case_dir / "label.json"
    label = json.loads(label_path.read_text(encoding="utf-8"))

    image_path = next(
        (case_dir / f for f in ["image.jpg", "image.jpeg", "image.png"] if (case_dir / f).exists()), None
    )
    if image_path is None:
        return {"case": case_dir.name, "error": "이미지 파일 없음", "skipped": True}

    provider = get_ocr_provider(config)
    raw_text = await provider.extract_text(str(image_path))
    parsed = _parse_with_openai(raw_text)
    pred = parsed.model_dump()

    scores = _score_case(pred, label)

    return {
        "case": case_dir.name,
        "skipped": False,
        "raw_ocr_length": len(raw_text),
        "scores": scores,
        "predicted": pred,
        "label": label,
    }


async def main():
    config = Config()  # type: ignore[call-arg]

    case_dirs = sorted(d for d in TESTCASES_DIR.iterdir() if d.is_dir() and (d / "label.json").exists())
    if not case_dirs:
        print("테스트 케이스 없음. testcases/case_NNN/image.jpg + label.json 추가 후 재실행")
        return

    print(f"[eval] OCR 평가 시작, 케이스: {len(case_dirs)}개\n")

    results = []
    for i, case_dir in enumerate(case_dirs, 1):
        print(f"  [{i:02d}/{len(case_dirs)}] {case_dir.name} ... ", end="", flush=True)
        result = await _run_case(case_dir, config)
        results.append(result)
        if result.get("skipped"):
            print(f"SKIP ({result.get('error', '')})")
        else:
            print(f"overall={result['scores']['overall']:.4f}")

    valid = [r for r in results if not r.get("skipped")]
    if valid:
        avg_field = round(sum(r["scores"]["field_accuracy"] for r in valid) / len(valid), 4)
        avg_med = round(sum(r["scores"]["medication_accuracy"] for r in valid) / len(valid), 4)
        avg_overall = round(sum(r["scores"]["overall"] for r in valid) / len(valid), 4)
    else:
        avg_field = avg_med = avg_overall = 0.0

    metrics = {
        "avg_field_accuracy": avg_field,
        "avg_medication_accuracy": avg_med,
        "avg_overall": avg_overall,
        "evaluated": len(valid),
        "skipped": len(results) - len(valid),
    }

    output = {
        "eval_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_cases": len(results),
        "metrics": metrics,
        "cases": results,
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    filename = RESULTS_DIR / f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    filename.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*50}")
    print(f"  필드 정확도     : {avg_field:.4f}")
    print(f"  약물 정확도     : {avg_med:.4f}")
    print(f"  종합 정확도     : {avg_overall:.4f}")
    print(f"{'='*50}")
    print(f"\n결과 저장: {filename}")


if __name__ == "__main__":
    asyncio.run(main())
