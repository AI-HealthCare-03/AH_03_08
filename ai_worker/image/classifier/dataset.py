# ai_worker/image/classifier/dataset.py

import csv
import glob
import json
import os
import random

PILL_DATA_PATH = "/Users/admin/Desktop/PyCharmProjects/Hackerton_Final_Project_공부/AI_Hub/AI 모델 소스코드/평가용 데이터셋/pill_data/pill_data_croped"
OUTPUT_DIR = "/Users/admin/PycharmProjects/AH_03_08/ai_worker/image/classifier"
IMAGES_PER_DRUG = 10
TRAIN_RATIO = 0.8
RANDOM_SEED = 42


def build_dataset():
    random.seed(RANDOM_SEED)

    drug_dirs = [d for d in os.listdir(PILL_DATA_PATH) if os.path.isdir(os.path.join(PILL_DATA_PATH, d))]
    random.shuffle(drug_dirs)

    split_idx = int(len(drug_dirs) * TRAIN_RATIO)
    train_drugs = drug_dirs[:split_idx]
    val_drugs = drug_dirs[split_idx:]

    print(f"전체: {len(drug_dirs)}종 | train: {len(train_drugs)}종 | val: {len(val_drugs)}종")

    for split, drugs in [("train", train_drugs), ("val", val_drugs)]:
        rows = []
        for drug in drugs:
            drug_path = os.path.join(PILL_DATA_PATH, drug)

            # JSON에서 라벨 추출 (첫 번째 JSON만)
            json_files = glob.glob(f"{drug_path}/*.json")
            if not json_files:
                continue
            with open(json_files[0], encoding="utf-8") as f:
                data = json.load(f)
            info = data["images"][0]
            color = (info.get("color_class1") or "").split(",")[0].strip()
            shape = info.get("drug_shape", "")

            if not color or not shape:
                continue

            # PNG 샘플링
            png_files = glob.glob(f"{drug_path}/*.png")
            sampled = random.sample(png_files, min(IMAGES_PER_DRUG, len(png_files)))

            for img_path in sampled:
                rows.append(
                    {
                        "image_path": img_path,
                        "color": color,
                        "shape": shape,
                    }
                )

        output_path = os.path.join(OUTPUT_DIR, f"{split}.csv")
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["image_path", "color", "shape"])
            writer.writeheader()
            writer.writerows(rows)

        print(f"{split}.csv 저장 완료 - {len(rows)}장")


if __name__ == "__main__":
    build_dataset()
