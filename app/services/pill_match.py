# app/services/pill_match.py

import re


def _normalize_print_code(text: str) -> str:
    """식별코드에서 '분할선' 제거 후 공백 strip."""
    return text.replace("분할선", "").strip()


def _build_normalized_index(print_index: dict) -> dict[str, list[str]]:
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
    matched = False
    for text in ocr_texts:
        text_upper = text.strip().upper()
        if text_upper in print_index:
            for kcode in print_index[text_upper]:
                scores[kcode] = scores.get(kcode, 0) + 3
            matched = True
    return matched


def _match_normalized(ocr_texts: list[str], print_index: dict, normalized_index: dict, scores: dict) -> bool:
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


def _build_candidates(sorted_kcodes: list[str], kcode_info: dict, scores: dict) -> list[dict]:
    candidates = []
    for kcode in sorted_kcodes:
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
                "color_class1": info.get("color_class1"),
                "drug_shape": info.get("drug_shape"),
                "chart": info.get("chart"),
                "dl_company": info.get("dl_company"),
                "score": scores[kcode],
            }
        )
    return candidates


def match_by_print_code(
    ocr_texts: list[str],
    print_index: dict,
    kcode_info: dict,
) -> tuple[list[dict], str] | None:
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

    sorted_kcodes = sorted(scores, key=lambda k: scores[k], reverse=True)[:5]
    candidates = _build_candidates(sorted_kcodes, kcode_info, scores)

    return (candidates, matched_method) if candidates else None

def rerank_by_color_shape(
    predicted_color: str,
    predicted_shape: str,
    candidates: list[dict],
) -> list[dict]:
    """
    색상/모양 예측 결과로 후보 약품 리스트를 재정렬한다.

    Args:
        predicted_color: 예측된 색상
        predicted_shape: 예측된 모양
        candidates: OCR 매칭 후보 리스트

    Returns:
        list[dict]: 재정렬된 후보 리스트
    """
    try:
        for candidate in candidates:
            bonus = 0
            if candidate.get("color_class1") == predicted_color:
                bonus += 2
            if candidate.get("drug_shape") == predicted_shape:
                bonus += 1
            candidate["score"] = candidate.get("score", 0) + bonus

        return sorted(candidates, key=lambda x: x["score"], reverse=True)

    except Exception:
        return candidates