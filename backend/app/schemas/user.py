from datetime import datetime
from uuid import UUID
from typing import Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=12,
        max_length=128,
    )
    display_name: str = Field(
        min_length=2,
        max_length=100,
    )
    country_code: str = Field(
        default="MX",
        pattern=r"^[A-Za-z]{2}$",
    )

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()

        return value

    @field_validator("display_name", mode="before")
    @classmethod
    def normalize_display_name(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.upper()


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=1,
        max_length=128,
    )

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()

        return value

class EmailVerificationConfirm(BaseModel):
    token: str = Field(
        min_length=32,
        max_length=256,
    )


class EmailVerificationResend(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()

        return value


class MessageResponse(BaseModel):
    message: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(gt=0)

class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str
    country_code: str
    is_active: bool
    is_email_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)