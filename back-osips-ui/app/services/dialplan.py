"""Работа с модулем dialplan: таблица dialplan в БД + dp_reload/dp_translate.

Проверено по исходникам OpenSIPS 3.6 (modules/dialplan):
  match_op:    0 - равенство строк (EQUAL_OP), 1 - регулярное выражение (REGEX_OP);
  match_flags: бит 1 - сравнение без учёта регистра (DP_CASE_INSENSITIVE);
  MI:          dp_reload([partition]), dp_translate(dpid, input[, partition]),
               dp_show_partition([partition]).

Интерфейс работает с таблицей `dialplan` - именем по умолчанию. Если в конфигурации
opensips для партиции задана другая таблица, правьте её через ту партицию, где она лежит.
"""

import logging
from typing import Any

from ..config import settings
from ..db.models import OpensipsServer
from . import mi, opensips_db, table_crud

logger = logging.getLogger("osips-ui")

TABLE = "dialplan"
COLUMNS = ("dpid", "pr", "match_op", "match_exp", "match_flags", "subst_exp", "repl_exp", "timerec", "disabled", "attrs")

EQUAL_OP = 0
REGEX_OP = 1
CASE_INSENSITIVE = 1  # DP_CASE_INSENSITIVE в match_flags


async def list_rules(
    server: OpensipsServer,
    *,
    page: int = 1,
    per_page: int | None = None,
    search: str | None = None,
    dpid: int | None = None,
    only_enabled: bool = False,
) -> dict[str, Any]:
    conditions: list[str] = []
    params: dict[str, Any] = {}
    if dpid is not None:
        conditions.append("dpid = :dpid")
        params["dpid"] = dpid
    if only_enabled:
        conditions.append("disabled = 0")
    if search:
        conditions.append("(match_exp LIKE :search OR subst_exp LIKE :search OR repl_exp LIKE :search OR attrs LIKE :search)")
        params["search"] = f"%{search}%"

    return await table_crud.fetch_page(
        server,
        TABLE,
        COLUMNS,
        where=" AND ".join(conditions),
        params=params,
        order_by="dpid, pr, id",
        page=page,
        per_page=per_page or settings.DIALPLAN_PAGE_SIZE,
    )


async def dpids(server: OpensipsServer) -> list[dict]:
    """Список dpid с количеством правил - для фильтра и подсказок в форме."""
    return await opensips_db.fetch_all(
        server,
        f"SELECT dpid, COUNT(*) AS rules, SUM(disabled = 0) AS enabled FROM {TABLE} GROUP BY dpid ORDER BY dpid",
    )


async def partitions(server: OpensipsServer) -> tuple[list[dict], str | None]:
    """Партиции dialplan из памяти opensips (dp_show_partition). Пусто, если MI недоступен."""
    if not mi.has_mi(server):
        return [], "http MI не настроен для этого сервера"
    try:
        result = await mi.call(server, "dp_show_partition")
    except mi.MIError as exc:
        logger.warning("dp_show_partition failed: %s", exc)
        return [], str(exc)
    items = (result or {}).get("Partitions", []) if isinstance(result, dict) else []
    return [item for item in items if isinstance(item, dict)], None


async def reload(server: OpensipsServer, partition: str | None = None) -> Any:
    """Без партиции opensips перечитывает все партиции dialplan."""
    return await mi.call(server, "dp_reload", {"partition": partition} if partition else None)


async def translate(server: OpensipsServer, dpid: int, value: str, partition: str | None = None) -> dict[str, Any]:
    """dp_translate: прогоняет строку через правила dpid так же, как это делает opensips."""
    params: dict[str, Any] = {"dpid": str(dpid), "input": value}
    if partition:
        params["partition"] = partition
    result = await mi.call(server, "dp_translate", params)
    if not isinstance(result, dict):
        return {"output": str(result), "attributes": None}
    return {"output": result.get("Output"), "attributes": result.get("ATTRIBUTES") or None}


async def get(server: OpensipsServer, row_id: int) -> dict | None:
    return await table_crud.get(server, TABLE, COLUMNS, row_id)


async def create(server: OpensipsServer, data: dict[str, Any]) -> int | None:
    return await table_crud.insert(server, TABLE, COLUMNS, data)


async def update(server: OpensipsServer, row_id: int, data: dict[str, Any]) -> int:
    return await table_crud.update(server, TABLE, COLUMNS, row_id, data)


async def delete(server: OpensipsServer, row_id: int) -> int:
    return await table_crud.delete(server, TABLE, row_id)
