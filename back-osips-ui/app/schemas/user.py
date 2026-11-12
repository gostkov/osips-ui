from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from .role import SLUG_PATTERN


def _check_password_bytes(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Пароль должен занимать не более 72 байт в UTF-8")
    return value


NewPassword = Annotated[
    str,
    Field(min_length=8, max_length=72, description="От 8 символов, не более 72 байт в UTF-8"),
    AfterValidator(_check_password_bytes),
]


class UserBase(BaseModel):
    username: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9._@-]+$")
    full_name: str | None = Field(default=None, max_length=128)
    email: str | None = Field(default=None, max_length=128)
    role: str = Field(default="reader", pattern=SLUG_PATTERN)
    is_active: bool = True


class UserCreate(UserBase):
    password: NewPassword


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=128)
    email: str | None = Field(default=None, max_length=128)
    role: str | None = Field(default=None, pattern=SLUG_PATTERN)
    is_active: bool | None = None
    password: NewPassword | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    auth_provider: str
    created_at: datetime
    last_login_at: datetime | None = None


class MeOut(UserOut):
    permissions: list[str] = []


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: MeOut


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: NewPassword
