from typing import Any

from pydantic import BaseModel, Field

# match_op: 0 - равенство строк, 1 - регулярное выражение (modules/dialplan/dialplan.h)
MatchOp = Field(default=0, ge=0, le=1)


class DialplanRuleOut(BaseModel):
    id: int
    dpid: int
    pr: int = 0
    match_op: int = 0
    match_exp: str
    match_flags: int = 0
    subst_exp: str | None = None
    repl_exp: str | None = None
    timerec: str | None = None
    disabled: int = 0
    attrs: str | None = None


class DialplanPage(BaseModel):
    items: list[DialplanRuleOut]
    total: int
    page: int
    per_page: int


class DialplanRuleIn(BaseModel):
    dpid: int = Field(ge=0)
    pr: int = 0
    match_op: int = MatchOp
    match_exp: str = Field(min_length=1, max_length=64)
    match_flags: int = Field(default=0, ge=0)
    subst_exp: str | None = Field(default=None, max_length=64)
    repl_exp: str | None = Field(default=None, max_length=32)
    timerec: str | None = Field(default=None, max_length=255)
    disabled: int = Field(default=0, ge=0, le=1)
    attrs: str | None = Field(default=None, max_length=255)


class DialplanRuleUpdate(BaseModel):
    dpid: int | None = Field(default=None, ge=0)
    pr: int | None = None
    match_op: int | None = Field(default=None, ge=0, le=1)
    match_exp: str | None = Field(default=None, min_length=1, max_length=64)
    match_flags: int | None = Field(default=None, ge=0)
    subst_exp: str | None = Field(default=None, max_length=64)
    repl_exp: str | None = Field(default=None, max_length=32)
    timerec: str | None = Field(default=None, max_length=255)
    disabled: int | None = Field(default=None, ge=0, le=1)
    attrs: str | None = Field(default=None, max_length=255)


class DialplanDpid(BaseModel):
    dpid: int
    rules: int = 0
    enabled: int = 0


class DialplanPartitions(BaseModel):
    items: list[dict[str, Any]]
    mi_available: bool
    mi_error: str | None = None


class TranslateIn(BaseModel):
    dpid: int = Field(ge=0)
    value: str = Field(min_length=1, max_length=255)
    partition: str | None = Field(default=None, max_length=64)


class TranslateOut(BaseModel):
    output: str | None = None
    attributes: str | None = None
