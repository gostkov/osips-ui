"""Работа с модулем load_balancer: таблица load_balancer в БД + состояние из lb_list."""

import logging
from typing import Any

from ..db.models import OpensipsServer
from . import mi, opensips_db

logger = logging.getLogger("osips-ui")

TABLE = "load_balancer"
COLUMNS = ("group_id", "dst_uri", "resources", "probe_mode", "attrs", "description")


def _state_from_mi(dest: dict) -> str:
    """Приводим флаги lb_list к тем же трём состояниям, что и у dispatcher.

    enabled=yes                      -> active   (зелёный)
    enabled=no,  auto-reenable=off   -> inactive (серый)   - выключен вручную
    enabled=no,  auto-reenable=on    -> probing  (красный) - выключен пробингом
    """
    enabled = str(dest.get("enabled", "")).lower() == "yes"
    if enabled:
        return "active"
    auto_reenable = str(dest.get("auto-reenable", "")).lower() == "on"
    return "probing" if auto_reenable else "inactive"


async def runtime_state(server: OpensipsServer) -> tuple[dict[int, dict], str | None]:
    if not mi.has_mi(server):
        return {}, "http MI не настроен для этого сервера"
    try:
        result = await mi.call(server, "lb_list")
    except mi.MIError as exc:
        logger.warning("lb_list failed: %s", exc)
        return {}, str(exc)

    states: dict[int, dict] = {}
    for dest in (result or {}).get("Destinations", []) if isinstance(result, dict) else []:
        try:
            dst_id = int(dest.get("id"))
        except (TypeError, ValueError):
            continue
        states[dst_id] = {
            "state": _state_from_mi(dest),
            "enabled": str(dest.get("enabled", "")).lower() == "yes",
            "auto_reenable": str(dest.get("auto-reenable", "")).lower() == "on",
            "uri": dest.get("uri"),
            "group": dest.get("group"),
            "resources": dest.get("Resources", []),
        }
    return states, None


async def list_destinations(server: OpensipsServer) -> dict[str, Any]:
    rows = await opensips_db.fetch_all(
        server,
        f"SELECT id, {', '.join(COLUMNS)} FROM {TABLE} ORDER BY group_id, id",
    )
    states, mi_error = await runtime_state(server)

    for row in rows:
        runtime = states.get(int(row["id"]))
        row["runtime_state"] = runtime["state"] if runtime else "unknown"
        row["runtime"] = runtime
    return {"rows": rows, "mi_available": mi_error is None, "mi_error": mi_error}


async def set_status(server: OpensipsServer, destination_id: int, enabled: bool) -> Any:
    return await mi.call(server, "lb_status", {"destination_id": destination_id, "new_status": 1 if enabled else 0})


async def reload(server: OpensipsServer) -> Any:
    return await mi.call(server, "lb_reload")


async def create(server: OpensipsServer, data: dict[str, Any]) -> int | None:
    fields = [column for column in COLUMNS if column in data]
    sql = f"INSERT INTO {TABLE} ({', '.join(fields)}) VALUES ({', '.join(':' + f for f in fields)})"
    result = await opensips_db.execute(server, sql, {field: data[field] for field in fields})
    return result["lastrowid"]


async def update(server: OpensipsServer, row_id: int, data: dict[str, Any]) -> int:
    fields = [column for column in COLUMNS if column in data]
    if not fields:
        return 0
    sql = f"UPDATE {TABLE} SET {', '.join(f'{f} = :{f}' for f in fields)} WHERE id = :id"
    params = {field: data[field] for field in fields} | {"id": row_id}
    result = await opensips_db.execute(server, sql, params)
    return result["rowcount"]


async def delete(server: OpensipsServer, row_id: int) -> int:
    result = await opensips_db.execute(server, f"DELETE FROM {TABLE} WHERE id = :id", {"id": row_id})
    return result["rowcount"]


async def get(server: OpensipsServer, row_id: int) -> dict | None:
    rows = await opensips_db.fetch_all(server, f"SELECT id, {', '.join(COLUMNS)} FROM {TABLE} WHERE id = :id", {"id": row_id})
    return rows[0] if rows else None
