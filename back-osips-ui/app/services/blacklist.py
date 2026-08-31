"""Работа с модулем userblacklist: таблицы userblacklist и globalblacklist.

Проверено по исходникам OpenSIPS 3.6 (modules/userblacklist):
  check_user_blacklist() строит дерево префиксов запросом в таблицу userblacklist на каждый
  вызов - правки в ней начинают действовать сразу, reload не нужен;
  check_blacklist() работает с таблицами-источниками (обычно globalblacklist), загруженными
  в память при старте - их применяет MI-команда reload_blacklist.

whitelist=1 в обеих таблицах означает "разрешающее правило": совпадение с ним снимает запрет.
"""

import logging
from typing import Any

from ..config import settings
from ..db.models import OpensipsServer
from . import mi, table_crud

logger = logging.getLogger("osips-ui")

USER_TABLE = "userblacklist"
GLOBAL_TABLE = "globalblacklist"

TABLES: dict[str, dict[str, Any]] = {
    "user": {
        "table": USER_TABLE,
        "columns": ("username", "domain", "prefix", "whitelist"),
        "search": ("username", "domain", "prefix"),
        "order_by": "username, domain, prefix, id",
        # правки применяются сразу, поэтому в UI не предлагаем reload
        "needs_reload": False,
    },
    "global": {
        "table": GLOBAL_TABLE,
        "columns": ("prefix", "whitelist", "description"),
        "search": ("prefix", "description"),
        "order_by": "prefix, id",
        "needs_reload": True,
    },
}


class UnknownListError(ValueError):
    pass


def spec(kind: str) -> dict[str, Any]:
    try:
        return TABLES[kind]
    except KeyError:
        raise UnknownListError(f"Неизвестный список: {kind}") from None


async def list_entries(
    server: OpensipsServer,
    kind: str,
    *,
    page: int = 1,
    per_page: int | None = None,
    search: str | None = None,
    only: str | None = None,
) -> dict[str, Any]:
    """only: black - только запрещающие правила, white - только разрешающие."""
    meta = spec(kind)
    conditions: list[str] = []
    params: dict[str, Any] = {}
    if only == "black":
        conditions.append("whitelist = 0")
    elif only == "white":
        conditions.append("whitelist = 1")
    if search:
        conditions.append("(" + " OR ".join(f"{column} LIKE :search" for column in meta["search"]) + ")")
        params["search"] = f"%{search}%"

    result = await table_crud.fetch_page(
        server,
        meta["table"],
        meta["columns"],
        where=" AND ".join(conditions),
        params=params,
        order_by=meta["order_by"],
        page=page,
        per_page=per_page or settings.BLACKLIST_PAGE_SIZE,
    )
    return result | {"kind": kind, "table": meta["table"], "needs_reload": meta["needs_reload"]}


async def reload(server: OpensipsServer) -> Any:
    """reload_blacklist перечитывает таблицы-источники (globalblacklist и другие)."""
    return await mi.call(server, "reload_blacklist")


async def get(server: OpensipsServer, kind: str, row_id: int) -> dict | None:
    meta = spec(kind)
    return await table_crud.get(server, meta["table"], meta["columns"], row_id)


async def create(server: OpensipsServer, kind: str, data: dict[str, Any]) -> int | None:
    meta = spec(kind)
    return await table_crud.insert(server, meta["table"], meta["columns"], data)


async def update(server: OpensipsServer, kind: str, row_id: int, data: dict[str, Any]) -> int:
    meta = spec(kind)
    return await table_crud.update(server, meta["table"], meta["columns"], row_id, data)


async def delete(server: OpensipsServer, kind: str, row_id: int) -> int:
    meta = spec(kind)
    return await table_crud.delete(server, meta["table"], row_id)
