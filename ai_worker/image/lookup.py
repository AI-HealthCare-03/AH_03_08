# ai_worker/image/lookup.py

# 표준 라이브러리
import glob
import json

# 로컬 모듈
from ai_worker.core.logger import logger


def get_kcode(class_idx: int, label_path: str) -> str:
    """
    클래스 인덱스를 K코드로 변환한다.

    Args:
        class_idx: 모델 출력 클래스 인덱스 (0~999)
        label_path: 라벨 파일 경로

    Returns:
        str: K코드 (예: "K-037589")
    """
    if not label_path:
        raise ValueError("PILL_LABEL_PATH 환경변수가 설정되지 않았습니다.")

    with open(label_path) as f:
        data = json.load(f)

    index_to_kcode = {item[0]: item[1] for item in data["pill_label_path_sharp_score"]}

    kcode = index_to_kcode.get(class_idx)
    if not kcode:
        raise ValueError(f"클래스 인덱스 {class_idx}에 해당하는 K코드가 없습니다.")

    logger.info(f"K코드 변환 완료 - class_idx: {class_idx} → kcode: {kcode}")
    return kcode


def get_drug_info(kcode: str, data_path: str) -> dict:
    """
    K코드로 AI Hub JSON DB에서 약품 정보를 조회한다.

    Args:
        kcode: K코드 (예: "K-037589")
        data_path: 약품 데이터 경로

    Returns:
        dict: 약품 상세 정보

    Note:
        - 개인정보 보호: 약품 정보 조회 시 K코드만 로그 기록
    """
    if not data_path:
        raise ValueError("PILL_DATA_PATH 환경변수가 설정되지 않았습니다.")

    json_files = glob.glob(f"{data_path}/{kcode}/*.json")

    if not json_files:
        raise ValueError(f"K코드 {kcode}에 해당하는 약품 정보가 없습니다.")

    with open(json_files[0], encoding="utf-8") as f:
        data = json.load(f)

    info = data["images"][0]

    logger.info(f"약품 정보 조회 완료 - kcode: {kcode}")

    return {
        "drug_name": info.get("dl_name"),
        "dl_company": info.get("dl_company"),
        "dl_material": info.get("dl_material"),
        "drug_shape": info.get("drug_shape"),
        "color_class1": info.get("color_class1"),
        "di_class_no": info.get("di_class_no"),
        "di_etc_otc_code": info.get("di_etc_otc_code"),
        "chart": info.get("chart"),
        "print_front": info.get("print_front"),
        "print_back": info.get("print_back"),
    }