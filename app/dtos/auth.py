from datetime import date
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, EmailStr, Field

from app.core.validators import validate_birthday, validate_password, validate_phone_number
from app.models.users import Gender


class AllergyInput(BaseModel):
    allergen_name: str = Field(..., max_length=200)
    severity: Literal["mild", "moderate", "severe"] = "mild"


class ConditionInput(BaseModel):
    condition_name: str = Field(..., max_length=200)
    severity: Literal["mild", "moderate", "severe"] = "mild"


class EmailSendRequest(BaseModel):
    email: EmailStr


class EmailVerifyRequest(BaseModel):
    email: EmailStr
    code: str


class SignUpRequest(BaseModel):
    email: Annotated[EmailStr, Field(None, max_length=40)]
    email_token: str | None = None
    password: Annotated[str, Field(min_length=8), AfterValidator(validate_password)]
    name: Annotated[str, Field(max_length=20)]
    gender: Gender
    birth_date: Annotated[date, AfterValidator(validate_birthday)]
    phone_number: Annotated[str, AfterValidator(validate_phone_number)]
    height_cm: float | None = None
    weight_kg: float | None = None
    allergies: list[AllergyInput] = []
    conditions: list[ConditionInput] = []


class LoginRequest(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=8)]


class LoginResponse(BaseModel):
    access_token: str
    is_admin: bool = False


class TokenRefreshResponse(BaseModel):
    access_token: str


class GoogleLoginRequest(BaseModel):
    code: str


class KakaoLoginRequest(BaseModel):
    code: str
