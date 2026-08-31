"""Работа с модулем rtpengine: таблица rtpengine в БД + состояние сокетов из rtpengine_show.

Проверено по исходникам OpenSIPS 3.6 (modules/rtpengine/rtpengine.c):
  rtpengine_show   -> [{"Set": N, "Nodes": [{"url", "index", "disabled", "weight", "recheck_ticks"}]}]
  rtpengine_enable(url, enable[, setid]) - enable: 0 выключить, 1 включить, 2 отложенно выключить
  rtpengine_reload([type=soft]) - работает, только если у модуля задан db_url

recheck_ticks == MI_MAX_RECHECK_TICKS ((unsigned)-1) означает "выключен насовсем" (руками через MI),
конечное значение - модуль сам выключил сокет и перепроверит его позже.
"""

import logging
from typing import Any

from ..db.models import OpensipsServer
from . import mi, table_crud

logger = logging.getLogger("osips-ui")

TABLE = "rtpengine"
COLUMNS = ("socket", "set_id")

MAX_RECHECK_TICKS = 4294967295  # (unsigned int)-1


def normalize_socket(socket: str | None) -> str:
    return (socket or "").strip().lower()


def _state(disabled: Any, recheck_ticks: Any) -> str:
    """active (работает) / inactive (выключен вручную) / probing (выключен модулем)."""
    try:
        is_disabled = int(disabled) != 0
    except (TypeError, ValueError):
        return "unknown"
    if not is_disabled:
        return "active"
    try:
        ticks = int(recheck_ticks)
    except (TypeError, ValueError):
        return "inactive"
    return "inactive" if ticks in (-1, MAX_RECHECK_TICKS) else "probing"


async def runtime_state(server: OpensipsServer) -> tuple[dict[tuple[int, str], dict], str | None]:
    """{(set_id, socket): {...}} по данным rtpengine_show."""
    if not mi.has_mi(server):
        return {}, "http MI не настроен для этого сервера"
    try:
        result = await mi.call(server, "rtpengine_show")
    except mi.MIError as exc:
        logger.warning("rtpengine_show failed: %s", exc)
        return {}, str(exc)

    states: dict[tuple[int, str], dict] = {}
    for rtpe_set in result or []:
        if not isinstance(rtpe_set, dict):
            continue
        try:
            set_id = int(rtpe_set.get("Set"))
        except (TypeError, ValueError):
            continue
        for node in rtpe_set.get("Nodes", []) or []:
            states[(set_id, normalize_socket(node.get("url")))] = {
                "state": _state(node.get("disabled"), node.get("recheck_ticks")),
                "index": node.get("index"),
                "weight": node.get("weight"),
                "recheck_ticks": node.get("recheck_ticks"),
                "disabled": node.get("disabled"),
            }
    return states, None


async def list_sockets(server: OpensipsServer) -> dict[str, Any]:
    rows = await table_crud.fetch(server, TABLE, COLUMNS, order_by="set_id, id")
    states, mi_error = await runtime_state(server)

    for row in rows:
        runtime = states.get((int(row["set_id"]), normalize_socket(row["socket"])))
        row["runtime_state"] = runtime["state"] if runtime else "unknown"
        row["runtime"] = runtime
    return {"rows": rows, "mi_available": mi_error is None, "mi_error": mi_error}


async def set_enabled(server: OpensipsServer, set_id: int, socket: str, enabled: bool) -> Any:
    return await mi.call(server, "rtpengine_enable", {"url": socket, "enable": 1 if enabled else 0, "setid": set_id})


async def reload(server: OpensipsServer, soft: bool = False) -> Any:
    """rtpengine_reload перечитывает таблицу; soft оставляет живые сокеты нетронутыми."""
    return await mi.call(server, "rtpengine_reload", {"type": "soft"} if soft else None)


async def get(server: OpensipsServer, row_id: int) -> dict | None:
    return await table_crud.get(server, TABLE, COLUMNS, row_id)


async def create(server: OpensipsServer, data: dict[str, Any]) -> int | None:
    return await table_crud.insert(server, TABLE, COLUMNS, data)


async def update(server: OpensipsServer, row_id: int, data: dict[str, Any]) -> int:
    return await table_crud.update(server, TABLE, COLUMNS, row_id, data)


async def delete(server: OpensipsServer, row_id: int) -> int:
    return await table_crud.delete(server, TABLE, row_id)
