from typing import Any

from pydantic import BaseModel, Field


class AddressTable(BaseModel):
    rows: list[dict[str, Any]]
    # записи, которые есть в памяти opensips, но которых нет в таблице (нужен address_reload)
    memory_only: list[dict[str, Any]] = []
    mi_available: bool
    mi_error: str | None = None


class AddressRowIn(BaseModel):
    grp: int = Field(default=0, ge=0, le=65535)
    ip: str = Field(min_length=1, max_length=50)
    mask: int = Field(default=32, ge=0, le=128)
    port: int = Field(default=0, ge=0, le=65535)
    proto: str = Field(default="any", max_length=4)
    pattern: str | None = Field(default=None, max_length=64)
    context_info: str | None = Field(default=None, max_length=32)


class AddressRowUpdate(BaseModel):
    grp: int | None = Field(default=None, ge=0, le=65535)
    ip: str | None = Field(default=None, min_length=1, max_length=50)
    mask: int | None = Field(default=None, ge=0, le=128)
    port: int | None = Field(default=None, ge=0, le=65535)
    proto: str | None = Field(default=None, max_length=4)
    pattern: str | None = Field(default=None, max_length=64)
    context_info: str | None = Field(default=None, max_length=32)


class AddressReloadIn(BaseModel):
    partition: str | None = Field(default=None, max_length=64)
