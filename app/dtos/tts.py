# app/dtos/tts.py

# 서드파티 라이브러리
from enum import Enum

from pydantic import BaseModel


# asset_type 허용 값 정의
# API 명세서: enum("tts", "card_image")
class AssetType(str, Enum):
    tts = "tts"
    card_image = "card_image"


# Request DTO: 클라이언트가 보내는 데이터
class GuideAssetCreateRequest(BaseModel):
    asset_type: AssetType  # "tts" or "card_image"


# Response DTO: 서버가 돌려주는 데이터
# API 명세서: { "asset_id": uuid, "status": str }
class GuideAssetCreateResponse(BaseModel):
    asset_id: str   # 생성된 asset ID
    status: str     # "processing" (Celery 작업 등록 완료)
