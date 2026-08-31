"""SIP-регистрации. Два источника на выбор:

* db - таблица location. Видна только при db_mode 2 (write-back) или 3 (write-through);
  при db_mode 0/1 таблица пустая, регистрации живут только в памяти.
* mi - команда ul_dump (память opensips). Актуальна при любом db_mode, но выгружает
  всю память целиком, поэтому на большой базе отвечает долго - таймаут MI_DUMP_TIMEOUT.

Смысл поля expires (см. modules/usrloc/ucontact.c): это абсолютный unix-time окончания
регистрации; 0 - постоянный контакт (чистка его не трогает), UL_EXPIRED_TIME=10 - контакт
принудительно помечен истёкшим. В ul_dump то же самое отдаётся уже разобранным:
число секунд до истечения либо строка permanent/expired/deleted (modules/usrloc/ul_mi.c).
"""

import time
from datetime import datetime, timedelta
from typing import Any

from ..config import settings
from ..db.models import OpensipsServer
from . import mi, opensips_db

TABLE = "location"
PERMANENT_EXPIRES = 0
FORCED_EXPIRED = 10  # UL_EXPIRED_TIME

COLUMNS = (
    "contact_id",
    "username",
    "domain",
    "contact",
    "received",
    "path",
    "expires",
    "q",
    "callid",
    "cseq",
    "last_modified",
    "flags",
    "cflags",
    "user_agent",
    "socket",
    "methods",
    "sip_instance",
    "kv_store",
    "attr",
)

_SELECT = ", ".join(COLUMNS) + ", FROM_UNIXTIME(expires) AS expires_at"


def _status(expires: int | None, now_ts: int) -> str:
    if expires == PERMANENT_EXPIRES:
        return "permanent"
    if expires is None or expires == FORCED_EXPIRED or expires <= now_ts:
        return "expired"
    return "active"


def _normalize(row: dict, now_ts: int) -> dict[str, Any]:
    expires = int(row["expires"]) if row.get("expires") is not None else None
    status = _status(expires, now_ts)
    username = row.get("username") or ""
    domain = row.get("domain") or ""
    return {
        "id": row.get("contact_id"),
        "username": username,
        "domain": domain,
        "aor": f"{username}@{domain}" if domain else username,
        "contact": row.get("contact") or "",
        "received": row.get("received"),
        "path": row.get("path"),
        "socket": row.get("socket"),
        "user_agent": row.get("user_agent"),
        "callid": row.get("callid"),
        "cseq": row.get("cseq"),
        "q": float(row["q"]) if row.get("q") is not None else None,
        "flags": row.get("flags"),
        "cflags": row.get("cflags"),
        "methods": row.get("methods"),
        "sip_instance": row.get("sip_instance"),
        "kv_store": row.get("kv_store"),
        "attr": row.get("attr"),
        "expires": expires,
        "expires_at": None if status == "permanent" else row.get("expires_at"),
        "expires_in": None if status == "permanent" or expires is None else expires - now_ts,
        "status": status,
        "last_modified": row.get("last_modified"),
    }


async def list_from_db(
    server: OpensipsServer,
    *,
    page: int = 1,
    per_page: int = 25,
    search: str | None = None,
    only_active: bool = False,
) -> dict[str, Any]:
    offset = (page - 1) * per_page

    conditions: list[str] = []
    params: dict[str, Any] = {}
    if search:
        conditions.append("(username LIKE :search OR contact LIKE :search OR received LIKE :search OR user_agent LIKE :search)")
        params["search"] = f"%{search}%"
    if only_active:
        conditions.append("(expires = 0 OR expires > UNIX_TIMESTAMP())")
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    summary = (
        await opensips_db.fetch_all(
            server,
            f"SELECT COUNT(*) AS total, COUNT(DISTINCT username) AS users, UNIX_TIMESTAMP() AS now_ts FROM {TABLE} {where}",
            params,
        )
    )[0]
    now_ts = int(summary["now_ts"])

    rows = await opensips_db.fetch_all(
        server,
        f"SELECT {_SELECT} FROM {TABLE} {where} ORDER BY username ASC, contact_id ASC LIMIT :limit OFFSET :offset",
        params | {"limit": per_page, "offset": offset},
    )

    return {
        "items": [_normalize(row, now_ts) for row in rows],
        "total": int(summary["total"]),
        "users": int(summary["users"]),
        "page": page,
        "per_page": per_page,
        "now_ts": now_ts,
    }


# --------------------------------------------------------------------------------------
# источник 2: MI ul_dump (память opensips)
# --------------------------------------------------------------------------------------

# в ul_dump поле Expires приходит строкой для особых случаев, иначе числом (секунд осталось)
_DUMP_STATUS = {"permanent": "permanent", "expired": "expired", "deleted": "expired"}


def _split_aor(aor: str) -> tuple[str, str]:
    username, _, domain = (aor or "").partition("@")
    return username, domain


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_dump(aor: str, contact: dict, table: str | None, now: float) -> dict[str, Any]:
    username, domain = _split_aor(aor)
    raw_expires = contact.get("Expires")
    if isinstance(raw_expires, str):
        status = _DUMP_STATUS.get(raw_expires.lower(), "expired")
        expires_in = None
    else:
        expires_in = _to_int(raw_expires)
        status = "active" if expires_in is not None and expires_in > 0 else "expired"

    return {
        "id": _to_int(contact.get("ContactID")),
        "username": username,
        "domain": domain,
        "aor": aor,
        "contact": contact.get("Contact") or "",
        "received": contact.get("Received"),
        "path": contact.get("Path"),
        "socket": contact.get("Socket"),
        "user_agent": contact.get("User-agent"),
        "callid": contact.get("Callid"),
        "cseq": _to_int(contact.get("Cseq")),
        "q": _to_float(contact.get("Q")),
        "flags": _to_int(contact.get("Flags")),
        "cflags": contact.get("Cflags") or None,
        "methods": _to_int(contact.get("Methods")),
        "sip_instance": contact.get("SIP_instance"),
        "attr": contact.get("Attr"),
        "expires": None,  # абсолютного времени ul_dump не отдаёт, только остаток
        "expires_at": None if expires_in is None else datetime.fromtimestamp(now + expires_in).replace(microsecond=0),
        "expires_in": expires_in,
        "status": status,
        "last_modified": None,  # в памяти этого поля нет, оно только в таблице location
        "state": contact.get("State"),
        "ping_latency": _to_int(contact.get("Ping-Latency")),
        "kv_store": contact.get("KV-Store"),
        "table": table,
    }


def flatten_dump(result: Any, now: float) -> list[dict[str, Any]]:
    """Разворачивает ответ ul_dump (Domains -> AORs -> Contacts) в плоский список контактов."""
    rows: list[dict[str, Any]] = []
    domains = (result or {}).get("Domains") or [] if isinstance(result, dict) else []
    for domain in domains:
        table = domain.get("name") if isinstance(domain, dict) else None
        for record in (domain.get("AORs") or []) if isinstance(domain, dict) else []:
            aor = record.get("AOR") or ""
            for contact in record.get("Contacts") or []:
                rows.append(_normalize_dump(aor, contact, table, now))
    return rows


def _matches(row: dict, search: str) -> bool:
    needle = search.lower()
    return any(
        needle in str(row.get(field) or "").lower() for field in ("username", "aor", "contact", "received", "user_agent")
    )


async def list_from_mi(
    server: OpensipsServer,
    *,
    page: int = 1,
    per_page: int = 25,
    search: str | None = None,
    only_active: bool = False,
) -> dict[str, Any]:
    now = time.time()
    result = await mi.call(server, "ul_dump", timeout=settings.MI_DUMP_TIMEOUT)
    rows = flatten_dump(result, now)

    if search:
        rows = [row for row in rows if _matches(row, search)]
    if only_active:
        rows = [row for row in rows if row["status"] != "expired"]
    rows.sort(key=lambda row: (row["username"], row["id"] or 0))

    offset = (page - 1) * per_page
    return {
        "items": rows[offset : offset + per_page],
        "total": len(rows),
        "users": len({row["aor"] for row in rows}),
        "page": page,
        "per_page": per_page,
        "now_ts": int(now),
    }


async def list_contacts(
    server: OpensipsServer,
    *,
    source: str = "db",
    page: int = 1,
    per_page: int = 25,
    search: str | None = None,
    only_active: bool = False,
) -> dict[str, Any]:
    lister = list_from_mi if source == "mi" else list_from_db
    data = await lister(server, page=page, per_page=per_page, search=search, only_active=only_active)
    return data | {"source": source}
