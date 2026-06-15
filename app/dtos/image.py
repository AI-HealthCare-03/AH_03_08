# app/dtos/image.py
from pydantic import BaseModel


class DrugInfoResponse(BaseModel):
    record_id: str
    status: str
    drug_name: str | None = None
    dl_company: str | None = None
    dl_material: str | None = None
    drug_shape: str | None = None
    color_class1: str | None = None
    color_class2: str | None = None
    di_class_no: str | None = None
    di_etc_otc_code: str | None = None
    chart: str | None = None
    print_front: str | None = None
    print_back: str | None = None
    disclaimer: str | None = "본 정보는 참고용이며, 정확한 복약 정보는 전문가에게 확인하세요."
    ocr_texts: list[str] = []


class PillMatchRequest(BaseModel):
    ocr_texts: list[str]
    predicted_color: str | None = None  # 추가
    predicted_shape: str | None = None  # 추가


class PillMatchResponse(BaseModel):
    matched: bool
    kcode: str | None = None
    drug_name: str | None = None
    dl_material: str | None = None
    di_class_no: str | None = None
    di_etc_otc_code: str | None = None
    print_front: str | None = None
    print_back: str | None = None
    color_class1: str | None = None
    color_class2: str | None = None
    drug_shape: str | None = None
    chart: str | None = None
    dl_company: str | None = None
    candidates: list[dict] | None = None
