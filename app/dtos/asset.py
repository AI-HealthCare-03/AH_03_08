# app/dtos/tts.py
# 서드파티 라이브러리
from enum import StrEnum

from pydantic import BaseModel


# asset_type 허용 값 정의
# API 명세서: enum("tts", "card_news")
class AssetType(StrEnum):
    tts = "tts"
    card_news = "card_news"  # card_image → card_news 변경


# Request DTO: 클라이언트가 보내는 데이터
class GuideAssetCreateRequest(BaseModel):
    asset_type: AssetType


# Response DTO: 서버가 돌려주는 데이터
# API 명세서: enum("tts", "card_news")
class GuideAssetCreateResponse(BaseModel):
    asset_id: str
    status: str
