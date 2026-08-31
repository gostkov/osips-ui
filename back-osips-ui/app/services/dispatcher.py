"""Работа с модулем dispatcher: таблица dispatcher в БД + состояние нод из ds_list."""

import logging
from typing import Any

from ..db.models import OpensipsServer
from . import mi, opensips_db

logger = logging.getLogger("osips-ui")

TABLE = "dispatcher"
COLUMNS = ("setid", "destination", "socket", "state", "probe_mode", "weight", "priority", "attrs", "description")

# состояние ноды в UI: active (зелёный) / inactive (серый) / probing (красный) / unknown (нет данных от MI)
_MI_STATE_MAP = {"active": "active", "inactive": "inactive", "probing": "probing"}
_STATE_TO_MI_ARG = {"active": "a", "inactive": "i", "probing": "p"}
# колонку state в таблице dispatcher opensips пишет сам (module param persistent_state), руками её не трогаем


def normalize_uri(uri: str | None) -> str:
    """Приводит destination к виду для сравнения БД <-> ds_list."""
    if not uri:
        return ""
    value = uri.strip().lower()
    if not value.startswith("sip:") and not value.startswith("sips:"):
        value = "sip:" + value
    return value


async def runtime_state(server: OpensipsServer) -> tuple[dict[tuple[int, str], dict], str | None]:
    """Возвращает ({(setid, uri): {...}}, error). error != None если MI недоступен."""
    if not mi.has_mi(server):
        return {}, "http MI не настроен для этого сервера"
    try:
        result = await mi.call(server, "ds_list", {"partition": server.dispatcher_partition or "default"})
    except mi.MIError as exc:
        logger.warning("ds_list failed: %s", exc)
        return {}, str(exc)

    states: dict[tuple[int, str], dict] = {}
    for partition in (result or {}).get("PARTITIONS", []) if isinstance(result, dict) else []:
        for ds_set in partition.get("SETS", []) or []:
            set_id = ds_set.get("id")
            for dest in ds_set.get("Destinations", []) or []:
                uri = normalize_uri(dest.get("URI"))
                states[(int(set_id), uri)] = {
                    "state": _MI_STATE_MAP.get(str(dest.get("state", "")).lower(), "unknown"),
                    "first_hit_counter": dest.get("first_hit_counter"),
                    "mi_weight": dest.get("weight"),
                    "mi_priority": dest.get("priority"),
                    "partition": partition.get("name"),
                }
    return states, None


async def list_destinations(server: OpensipsServer) -> dict[str, Any]:
    rows = await opensips_db.fetch_all(
        server,
        f"SELECT id, {', '.join(COLUMNS)} FROM {TABLE} ORDER BY setid, priority DESC, id",
    )
    states, mi_error = await runtime_state(server)

    for row in rows:
        runtime = states.get((int(row["setid"]), normalize_uri(row["destination"])))
        row["runtime_state"] = runtime["state"] if runtime else "unknown"
        row["runtime"] = runtime
    return {"rows": rows, "mi_available": mi_error is None, "mi_error": mi_error}


async def set_state(server: OpensipsServer, setid: int, destination: str, state: str) -> Any:
    if state not in _STATE_TO_MI_ARG:
        raise ValueError(f"Недопустимое состояние: {state}")
    group = str(setid)
    partition = server.dispatcher_partition or "default"
    if partition and partition != "default":
        group = f"{partition}:{setid}"
    return await mi.call(server, "ds_set_state", {"state": _STATE_TO_MI_ARG[state], "group": group, "address": destination})


async def reload(server: OpensipsServer) -> Any:
    params = {}
    if server.dispatcher_partition and server.dispatcher_partition != "default":
        params["partition"] = server.dispatcher_partition
    return await mi.call(server, "ds_reload", params or None)


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
