from typing import Any, Literal

from pydantic import BaseModel, Field

# user - таблица userblacklist (правила на абонента), global - globalblacklist (общие префиксы)
ListKind = Literal["user", "global"]


class BlacklistPage(BaseModel):
    kind: ListKind
    table: str
    needs_reload: bool
    items: list[dict[str, Any]]
    total: int
    page: int
    per_page: int


class UserBlacklistIn(BaseModel):
    username: str = Field(default="", max_length=64)
    domain: str = Field(default="", max_length=64)
    prefix: str = Field(default="", max_length=64)
    whitelist: int = Field(default=0, ge=0, le=1)


class UserBlacklistUpdate(BaseModel):
    username: str | None = Field(default=None, max_length=64)
    domain: str | None = Field(default=None, max_length=64)
    prefix: str | None = Field(default=None, max_length=64)
    whitelist: int | None = Field(default=None, ge=0, le=1)


class GlobalBlacklistIn(BaseModel):
    prefix: str = Field(default="", max_length=64)
    whitelist: int = Field(default=0, ge=0, le=1)
    description: str | None = Field(default=None, max_length=255)


class GlobalBlacklistUpdate(BaseModel):
    prefix: str | None = Field(default=None, max_length=64)
    whitelist: int | None = Field(default=None, ge=0, le=1)
    description: str | None = Field(default=None, max_length=255)
