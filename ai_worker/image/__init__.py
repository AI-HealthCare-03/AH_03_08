# ai_worker/image/__init__.py

import json

from ai_worker.core.config import Config
from ai_worker.image.lookup import get_drug_info, get_kcode
from ai_worker.image.model import load_model, predict
from ai_worker.image.preprocessor import preprocess_image


def load_print_index(index_path: str) -> dict:
    """식별코드 인덱스 파일을 로드한다."""
    with open(index_path, encoding="utf-8") as f:
        return json.load(f)


def match_by_print_code(ocr_texts: list[str], print_index: dict, kcode_info: dict) -> tuple[str, dict] | None:
    """
    OCR 추출 텍스트로 식별코드 인덱스에서 약품을 매칭한다.

    Args:
        ocr_texts: OCR로 추출된 텍스트 목록
        print_index: 식별코드 → K코드 목록 인덱스
        kcode_info: K코드 → 약품 정보

    Returns:
        tuple[str, dict] | None: (K코드, 약품 정보) 또는 None
    """
    candidates = {}
    for text in ocr_texts:
        text_upper = text.strip().upper()
        if text_upper in print_index:
            for kcode in print_index[text_upper]:
                candidates[kcode] = candidates.get(kcode, 0) + 1

    if not candidates:
        return None

    # 매칭 횟수가 가장 많은 K코드 선택
    best_kcode = max(candidates, key=lambda k: candidates[k])
    info = kcode_info.get(best_kcode)
    if not info:
        return None

    drug_info = {
        "drug_name": info["dl_name"],
        "dl_material": info["dl_material"],
        "di_class_no": info["di_class_no"],
        "di_etc_otc_code": info["di_etc_otc_code"],
        "print_front": info["print_front"],
        "print_back": info["print_back"],
    }
    return best_kcode, drug_info


class PillClassifier:
    """낱알약 이미지 분류 파이프라인."""

    def __init__(self, model_path: str, label_path: str, data_path: str, print_index_path: str = "") -> None:
        self.model = load_model(model_path)
        self.label_path = label_path
        self.data_path = data_path
        self.print_index = None
        self.kcode_info = None
        if print_index_path:
            index_data = load_print_index(print_index_path)
            self.print_index = index_data.get("print_index", {})
            self.kcode_info = index_data.get("kcode_info", {})

    def classify(self, image_bytes: bytes) -> tuple[str, dict, float]:
        """
        이미지를 분류하여 K코드, 약품 정보, confidence score를 반환한다.

        Args:
            image_bytes: 사용자가 업로드한 이미지 파일 (bytes)

        Returns:
            tuple[str, dict, float]: (K코드, 약품 정보, confidence score)
        """
        tensor = preprocess_image(image_bytes)
        class_idx, confidence_score = predict(self.model, tensor)
        kcode = get_kcode(class_idx, self.label_path)
        drug_info = get_drug_info(kcode, self.data_path)
        return kcode, drug_info, confidence_score

    def classify_with_ocr(self, image_bytes: bytes, ocr_texts: list[str]) -> tuple[str, dict, float, str]:
        """
        OCR 결과를 우선 활용하여 약품을 분류한다.

        Args:
            image_bytes: 사용자가 업로드한 이미지 파일 (bytes)
            ocr_texts: CLOVA OCR로 추출된 텍스트 목록

        Returns:
            tuple[str, dict, float, str]: (K코드, 약품 정보, confidence score, 분류 방법)
            분류 방법: "ocr" | "resnet"
        """
        # OCR 매칭 시도
        if self.print_index and ocr_texts:
            result = match_by_print_code(ocr_texts, self.print_index, self.kcode_info)
            if result:
                kcode, drug_info = result
                return kcode, drug_info, 1.0, "ocr"

        # OCR 실패 시 ResNet152 fallback
        kcode, drug_info, confidence_score = self.classify(image_bytes)
        return kcode, drug_info, confidence_score, "resnet"


def get_image_classifier(config: Config) -> PillClassifier:
    """config에서 값을 주입받아 PillClassifier를 반환한다."""
    return PillClassifier(
        model_path=config.PILL_MODEL_PATH,
        label_path=config.PILL_LABEL_PATH,
        data_path=config.PILL_DATA_PATH,
        print_index_path=config.PILL_PRINT_INDEX_PATH,
    )