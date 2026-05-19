from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSerializerModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={UUID: str},  # UUID → string 자동 변환
    )
