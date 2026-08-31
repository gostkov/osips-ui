from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ..core.roles import Perm

SLUG_PATTERN = r"^[a-z][a-z0-9._-]{1,31}$"


class RoleBase(BaseModel):
    title: str = Field(min_length=2, max_length=64)
    description: str | None = Field(default=None, max_length=255)


class RoleCreate(RoleBase):
    slug: str = Field(pattern=SLUG_PATTERN)
    permissions: list[Perm] = []


class RoleUpdate(BaseModel):
    slug: str | None = Field(default=None, pattern=SLUG_PATTERN)
    title: str | None = Field(default=None, min_length=2, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    permissions: list[Perm] | None = None


class RoleOut(RoleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    is_builtin: bool
    permissions: list[str] = []
    users_count: int = 0
    created_at: datetime | None = None


class RoleBrief(BaseModel):
    """Короткая карточка для выпадающего списка в форме пользователя."""

    slug: str
    title: str


class PermissionOut(BaseModel):
    value: str
    title: str


class PermissionGroupOut(BaseModel):
    section: str
    permissions: list[PermissionOut]
