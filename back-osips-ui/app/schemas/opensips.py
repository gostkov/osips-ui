from typing import Any, Literal

from pydantic import BaseModel, Field

NodeState = Literal["active", "inactive", "probing"]


class TableResponse(BaseModel):
    rows: list[dict[str, Any]]
    mi_available: bool
    mi_error: str | None = None


class DispatcherRowIn(BaseModel):
    setid: int = Field(ge=0)
    destination: str = Field(min_length=1, max_length=192)
    socket: str | None = Field(default=None, max_length=128)
    state: int = Field(default=0, ge=0, le=2)
    probe_mode: int = Field(default=0, ge=0, le=2)
    weight: str = Field(default="1", max_length=64)
    priority: int = 0
    attrs: str | None = Field(default=None, max_length=128)
    description: str | None = Field(default=None, max_length=64)


class DispatcherRowUpdate(BaseModel):
    setid: int | None = Field(default=None, ge=0)
    destination: str | None = Field(default=None, min_length=1, max_length=192)
    socket: str | None = Field(default=None, max_length=128)
    state: int | None = Field(default=None, ge=0, le=2)
    probe_mode: int | None = Field(default=None, ge=0, le=2)
    weight: str | None = Field(default=None, max_length=64)
    priority: int | None = None
    attrs: str | None = Field(default=None, max_length=128)
    description: str | None = Field(default=None, max_length=64)


class DispatcherStateIn(BaseModel):
    state: NodeState


class LoadBalancerRowIn(BaseModel):
    group_id: int = Field(default=0, ge=0)
    dst_uri: str = Field(min_length=1, max_length=128)
    resources: str = Field(min_length=1, max_length=255)
    probe_mode: int = Field(default=0, ge=0, le=2)
    attrs: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=128)


class LoadBalancerRowUpdate(BaseModel):
    group_id: int | None = Field(default=None, ge=0)
    dst_uri: str | None = Field(default=None, min_length=1, max_length=128)
    resources: str | None = Field(default=None, min_length=1, max_length=255)
    probe_mode: int | None = Field(default=None, ge=0, le=2)
    attrs: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=128)


class LoadBalancerStatusIn(BaseModel):
    enabled: bool


class ActionResult(BaseModel):
    ok: bool = True
    detail: Any = None
