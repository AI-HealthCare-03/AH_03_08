"""
약품 JSON DB에서 print_front/print_back 인덱스 파일 생성 스크립트
실행: python build_pill_index.py
출력: pill_print_index.json
"""

import json
from pathlib import Path

# 로컬 JSON DB 경로 — 실행 전 본인 환경에 맞게 수정하세요
JSON_DB_PATH = "/Users/admin/Desktop/PyCharmProjects/Hackerton_Final_Project_공부/AI_Hub/라벨링_JSON/output"
OUTPUT_PATH = "pill_print_index.json"


def build_index():  # noqa: C901
    print_index = {}
    kcode_info = {}

    kcode_dirs = [d for d in Path(JSON_DB_PATH).iterdir() if d.is_dir()]
    print(f"총 약품 폴더 수: {len(kcode_dirs)}")

    for kcode_dir in kcode_dirs:
        json_files = list(kcode_dir.glob("*.json"))
        if not json_files:
            continue

        with open(json_files[0], encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                continue

        images = data.get("images", [])
        if not images:
            continue

        img = images[0]
        kcode = img.get("dl_mapping_code", "")
        if not kcode:
            continue

        print_front = (img.get("print_front") or "").strip().upper()
        print_back = (img.get("print_back") or "").strip().upper()
        dl_name = img.get("dl_name", "")
        dl_material = img.get("dl_material", "")
        di_class_no = img.get("di_class_no", "")
        di_etc_otc_code = img.get("di_etc_otc_code", "")
        dl_company = img.get("dl_company", "")
        color_class1 = img.get("color_class1", "")
        color_class2 = img.get("color_class2", "")
        drug_shape = img.get("drug_shape", "")
        chart = img.get("chart", "")

        kcode_info[kcode] = {
            "dl_name": dl_name,
            "print_front": print_front,
            "print_back": print_back,
            "dl_material": dl_material,
            "di_class_no": di_class_no,
            "di_etc_otc_code": di_etc_otc_code,
            "dl_company": dl_company,
            "color_class1": color_class1,
            "color_class2": color_class2,
            "drug_shape": drug_shape,
            "chart": chart,
        }

        for text in [print_front, print_back]:
            if text:
                if text not in print_index:
                    print_index[text] = []
                if kcode not in print_index[text]:
                    print_index[text].append(kcode)

    result = {
        "print_index": print_index,
        "kcode_info": kcode_info,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"완료! 총 {len(kcode_info)}개 약품 인덱싱")
    print(f"식별코드 종류: {len(print_index)}개")
    print(f"저장 위치: {OUTPUT_PATH}")

    tylenol = print_index.get("TYLENOL", [])
    print(f"\nTYLENOL 매칭 약품: {tylenol}")
    for k in tylenol:
        print(f"  {k}: {kcode_info[k]['dl_name']}")


if __name__ == "__main__":
    build_index()
