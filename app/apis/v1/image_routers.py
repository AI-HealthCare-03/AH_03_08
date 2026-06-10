import json
from app.core.config import config
from app.dtos.image import PillMatchRequest, PillMatchResponse

@image_router.post(
    "/pill-match",
    response_model=PillMatchResponse,
    status_code=status.HTTP_200_OK,
)
async def match_pill_by_ocr(
    request: PillMatchRequest,
    current_user: Annotated[User, Depends(get_request_user)],
) -> PillMatchResponse:
    """
    OCR 식별코드로 약품 매칭 엔드포인트.
    사용자가 식별코드 수정 후 재매칭 시 사용.
    """
    try:
        with open(config.PILL_PRINT_INDEX_PATH, encoding="utf-8") as f:
            index_data = json.load(f)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="인덱스 파일을 불러올 수 없습니다.")

    print_index = index_data.get("print_index", {})
    kcode_info = index_data.get("kcode_info", {})

    candidates: dict[str, int] = {}
    for text in request.ocr_texts:
        text_upper = text.strip().upper()
        if text_upper in print_index:
            for kcode in print_index[text_upper]:
                candidates[kcode] = candidates.get(kcode, 0) + 1

    if not candidates:
        return PillMatchResponse(matched=False)

    best_kcode = max(candidates, key=lambda k: candidates[k])
    info = kcode_info.get(best_kcode)
    if not info:
        return PillMatchResponse(matched=False)

    return PillMatchResponse(
        matched=True,
        kcode=best_kcode,
        drug_name=info.get("dl_name"),
        dl_material=info.get("dl_material"),
        di_class_no=info.get("di_class_no"),
        di_etc_otc_code=info.get("di_etc_otc_code"),
        print_front=info.get("print_front"),
        print_back=info.get("print_back"),
    )