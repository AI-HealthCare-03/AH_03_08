# ai_worker/image/__init__.py

import json
import re

from ai_worker.core.config import Config
from ai_worker.core.logger import logger
from ai_worker.image.classifier import load_color_shape_model, predict_color_shape
from ai_worker.image.classifier.model import ColorShapeClassifier
from ai_worker.image.lookup import get_drug_info, get_kcode
from ai_worker.image.model import load_model, predict
from ai_worker.image.preprocessor import preprocess_image


def load_print_index(index_path: str) -> dict:
    """식별코드 인덱스 파일을 로드한다."""
    with open(index_path, encoding="utf-8") as f:
        return json.load(f)


def _normalize_print_code(text: str) -> str:
    """식별코드에서 '분할선' 제거 후 공백 strip."""
    return text.replace("분할선", "").strip()


def _build_normalized_index(print_index: dict) -> dict[str, list[str]]:
    """
    원본 print_index를 normalize한 역방향 인덱스를 빌드한다.
    normalize 결과가 빈 문자열이거나 순수 한글인 경우 제외.
    """
    normalized: dict[str, list[str]] = {}
    for key in print_index:
        norm = _normalize_print_code(key)
        if not norm:
            continue
        if re.fullmatch(r"[가-힣\s]+", norm):
            continue
        norm_upper = norm.upper()
        if norm_upper not in normalized:
            normalized[norm_upper] = []
        if key not in normalized[norm_upper]:
            normalized[norm_upper].append(key)
    return normalized


def _match_exact(ocr_texts: list[str], print_index: dict, scores: dict) -> bool:
    """1단계: 완전 일치 매칭 (가중치 3). 매칭 발생 시 True 반환."""
    matched = False
    for text in ocr_texts:
        text_upper = text.strip().upper()
        if text_upper in print_index:
            for kcode in print_index[text_upper]:
                scores[kcode] = scores.get(kcode, 0) + 3
            matched = True
    return matched


def _match_normalized(ocr_texts: list[str], print_index: dict, normalized_index: dict, scores: dict) -> bool:
    """2단계: 분할선 제거 후 normalize 매칭 (가중치 2). 매칭 발생 시 True 반환."""
    matched = False
    for text in ocr_texts:
        text_upper = text.strip().upper()
        if text_upper in print_index:
            continue
        norm = _normalize_print_code(text_upper)
        if norm and norm in normalized_index:
            for orig_key in normalized_index[norm]:
                for kcode in print_index[orig_key]:
                    scores[kcode] = scores.get(kcode, 0) + 2
            matched = True
    return matched


def _match_partial(ocr_texts: list[str], print_index: dict, scores: dict) -> bool:
    """3단계: 부분 문자열 포함 검색 fallback (가중치 1, 2글자 이상만). 매칭 발생 시 True 반환."""
    matched = False
    for text in ocr_texts:
        text_upper = text.strip().upper()
        if len(text_upper) < 2:
            continue
        for key in print_index:
            norm_key = _normalize_print_code(key).upper()
            if text_upper in norm_key or norm_key in text_upper:
                for kcode in print_index[key]:
                    scores[kcode] = scores.get(kcode, 0) + 1
                matched = True
    return matched


def _build_candidates(sorted_k_codes: list[str], kcode_info: dict, scores: dict) -> list[dict]:
    """K코드 목록으로 후보 약품 리스트를 빌드한다."""
    candidates = []
    for kcode in sorted_k_codes:
        info = kcode_info.get(kcode)
        if not info:
            continue
        candidates.append(
            {
                "kcode": kcode,
                "drug_name": info["dl_name"],
                "dl_material": info["dl_material"],
                "di_class_no": info["di_class_no"],
                "di_etc_otc_code": info["di_etc_otc_code"],
                "print_front": info["print_front"],
                "print_back": info["print_back"],
                "color_class1": info.get("color_class1", ""),
                "drug_shape": info.get("drug_shape", ""),
                "score": scores[kcode],
            }
        )
    return candidates


def match_by_print_code(
    ocr_texts: list[str],
    print_index: dict,
    kcode_info: dict,
) -> tuple[list[dict], str] | None:
    """
    OCR 추출 텍스트로 식별코드 인덱스에서 약품을 매칭한다.

    매칭 전략 (우선순위 순):
    1. 완전 일치 (original key, 가중치 3)
    2. normalize 후 일치 — 분할선 제거 (가중치 2)
    3. 부분 문자열 포함 검색 fallback (가중치 1, 2글자 이상만)
    """
    if not ocr_texts:
        return None

    normalized_index = _build_normalized_index(print_index)
    scores: dict[str, int] = {}

    exact_hit = _match_exact(ocr_texts, print_index, scores)
    norm_hit = _match_normalized(ocr_texts, print_index, normalized_index, scores)

    if not scores:
        _match_partial(ocr_texts, print_index, scores)
        matched_method = "partial" if scores else None
    elif exact_hit:
        matched_method = "exact"
    else:
        matched_method = "normalized" if norm_hit else None

    if not scores or not matched_method:
        return None

    sorted_k_codes = sorted(scores, key=lambda k: scores[k], reverse=True)[:5]
    candidates = _build_candidates(sorted_k_codes, kcode_info, scores)

    return (candidates, matched_method) if candidates else None


def rerank_by_color_shape(
    image_bytes: bytes,
    candidates: list[dict],
    color_shape_model: ColorShapeClassifier,
    color_classes: list[str],
    shape_classes: list[str],
) -> list[dict]:
    """
    색상/모양 분류기로 후보 약품 리스트를 재정렬한다.

    Args:
        image_bytes: 업로드된 이미지 bytes
        candidates: OCR 매칭 후보 리스트
        color_shape_model: 색상/모양 분류 모델
        color_classes: 색상 클래스 목록
        shape_classes: 모양 클래스 목록

    Returns:
        list[dict]: 재정렬된 후보 리스트
    """
    try:
        predicted_color, predicted_shape, color_conf, shape_conf = predict_color_shape(
            color_shape_model, image_bytes, color_classes, shape_classes
        )
        logger.info(
            f"색상/모양 예측 - color: {predicted_color}({color_conf:.2f}), "
            f"shape: {predicted_shape}({shape_conf:.2f})"
        )

        for candidate in candidates:
            bonus = 0
            if candidate.get("color_class1") == predicted_color:
                bonus += 2
            if candidate.get("drug_shape") == predicted_shape:
                bonus += 1
            candidate["score"] = candidate.get("score", 0) + bonus

        return sorted(candidates, key=lambda x: x["score"], reverse=True)

    except Exception as exc:
        logger.warning(f"색상/모양 재정렬 실패: {exc}")
        return candidates


class PillClassifier:
    """낱알약 이미지 분류 파이프라인."""

    def __init__(
        self,
        model_path: str,
        label_path: str,
        data_path: str,
        print_index_path: str = "",
        color_shape_model_path: str = "",
    ) -> None:
        self.model = load_model(model_path)
        self.label_path = label_path
        self.data_path = data_path
        self.print_index: dict | None = None
        self.kcode_info: dict | None = None
        self.color_shape_model: ColorShapeClassifier | None = None
        self.color_classes: list[str] | None = None
        self.shape_classes: list[str] | None = None

        if print_index_path:
            index_data = load_print_index(print_index_path)
            self.print_index = index_data.get("print_index", {})
            self.kcode_info = index_data.get("kcode_info", {})

        if color_shape_model_path:
            self.color_shape_model, self.color_classes, self.shape_classes = load_color_shape_model(
                color_shape_model_path
            )
            logger.info("색상/모양 분류 모델 로드 완료")

    def classify(self, image_bytes: bytes) -> tuple[str, dict, float]:
        """
        이미지를 분류하여 K코드, 약품 정보, confidence score를 반환한다.
        """
        tensor = preprocess_image(image_bytes)
        class_idx, confidence_score = predict(self.model, tensor)
        kcode = get_kcode(class_idx, self.label_path)
        drug_info = get_drug_info(kcode, self.data_path)
        return kcode, drug_info, confidence_score

    def classify_with_ocr(
        self,
        image_bytes: bytes,
        ocr_texts: list[str],
    ) -> tuple[str, dict, float, str, list[dict] | None]:
        """
        OCR 결과를 우선 활용하여 약품을 분류한다.
        """
        if self.print_index and ocr_texts:
            result = match_by_print_code(ocr_texts, self.print_index, self.kcode_info or {})
            if result:
                candidates, ocr_method = result

                # 색상/모양 모델로 재정렬
                if (
                    self.color_shape_model is not None
                    and self.color_classes is not None
                    and self.shape_classes is not None
                    and len(candidates) > 1
                ):
                    candidates = rerank_by_color_shape(
                        image_bytes, candidates,
                        self.color_shape_model, self.color_classes, self.shape_classes
                    )

                best = candidates[0]
                drug_info = {
                    "drug_name": best["drug_name"],
                    "dl_material": best["dl_material"],
                    "di_class_no": best["di_class_no"],
                    "di_etc_otc_code": best["di_etc_otc_code"],
                    "print_front": best["print_front"],
                    "print_back": best["print_back"],
                }
                candidates_out = candidates if len(candidates) > 1 else None
                method = f"ocr_{ocr_method}" if len(candidates) == 1 else "ocr_candidates"
                return best["kcode"], drug_info, 1.0, method, candidates_out

        # OCR 실패 시 ResNet152 fallback
        kcode, drug_info, confidence_score = self.classify(image_bytes)
        return kcode, drug_info, confidence_score, "resnet", None


def get_image_classifier(config: Config) -> PillClassifier:
    """config에서 값을 주입받아 PillClassifier를 반환한다."""
    return PillClassifier(
        model_path=config.PILL_MODEL_PATH,
        label_path=config.PILL_LABEL_PATH,
        data_path=config.PILL_DATA_PATH,
        print_index_path=config.PILL_PRINT_INDEX_PATH,
        color_shape_model_path=getattr(config, "COLOR_SHAPE_MODEL_PATH", ""),
    )