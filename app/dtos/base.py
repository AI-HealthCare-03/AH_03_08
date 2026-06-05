from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSerializerModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={UUID: str},
    )


class BaseResponse(BaseModel, Generic[T]):
    """공통 응답 포맷 { success, data, message }"""

    success: bool = True
    data: T | None = None
    message: str = ""


class ErrorResponse(BaseModel):
    success: bool = False
    data: None = None
    message: str
    error_detail: str | None = None
