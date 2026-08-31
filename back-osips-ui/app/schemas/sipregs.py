from datetime import datetime
from typing import Literal

from pydantic import BaseModel

RegStatus = Literal["active", "expired", "permanent"]
RegSource = Literal["db", "mi"]


class RegistrationOut(BaseModel):
    id: int | None = None
    username: str
    domain: str | None = None
    aor: str
    contact: str
    received: str | None = None
    path: str | None = None
    socket: str | None = None
    user_agent: str | None = None
    callid: str | None = None
    cseq: int | None = None
    q: float | None = None
    flags: int | None = None
    cflags: str | None = None
    methods: int | None = None
    sip_instance: str | None = None
    kv_store: str | None = None
    attr: str | None = None
    expires: int | None = None
    expires_at: datetime | str | None = None
    expires_in: int | None = None  # секунд до истечения, отрицательное - уже истекла
    status: RegStatus
    last_modified: datetime | str | None = None
    # только для источника ul_dump - в таблице location этих полей нет
    state: str | None = None
    ping_latency: int | None = None
    table: str | None = None


class RegistrationPage(BaseModel):
    source: RegSource
    items: list[RegistrationOut]
    total: int
    users: int  # уникальных абонентов с учётом фильтра
    page: int
    per_page: int
