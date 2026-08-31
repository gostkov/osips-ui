"""Работа с модулем permissions: таблица address + дамп загруженного в память списка.

Проверено по исходникам OpenSIPS 3.6 (modules/permissions):
  address_dump([partition]) -> {"Partitions": [{"name", "Destinations": [{grp, ip, mask, port,
                               proto, pattern, context_info}]}]} - только точные адреса;
  subnet_dump([partition])  -> то же самое, но только подсети;
  address_reload([partition]) - перечитать таблицу.

В дампе маска подсети печатается в точечном виде (255.255.255.0), а в таблице лежит длина
префикса - при сравнении приводим к длине префикса.
"""

import ipaddress
import logging
from typing import Any

from ..db.models import OpensipsServer
from . import mi, table_crud

logger = logging.getLogger("osips-ui")

TABLE = "address"
COLUMNS = ("grp", "ip", "mask", "port", "proto", "pattern", "context_info")

PROTOCOLS = ("any", "udp", "tcp", "tls", "sctp", "ws", "wss")


def _prefix_len(value: Any, ip: str = "") -> int | None:
    """Длина префикса из числа ('24') или из точечной маски ('255.255.255.0')."""
    text = str(value or "").strip()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    try:
        return ipaddress.ip_network(f"{ip or '0.0.0.0'}/{text}", strict=False).prefixlen
    except ValueError:
        logger.debug("не разобрал маску %r", text)
        return None


def _key(grp: Any, ip: Any, mask: Any, port: Any, proto: Any) -> tuple:
    """Ключ сравнения строки таблицы и записи из памяти opensips."""
    ip_text = str(ip or "").strip().lower()
    return (
        int(grp or 0),
        ip_text,
        _prefix_len(mask, ip_text),
        int(port or 0),
        str(proto or "any").strip().lower(),
    )


async def runtime_state(server: OpensipsServer) -> tuple[dict[tuple, dict], str | None]:
    """{ключ: запись} по address_dump + subnet_dump (адреса и подсети лежат в разных таблицах)."""
    if not mi.has_mi(server):
        return {}, "http MI не настроен для этого сервера"

    entries: dict[tuple, dict] = {}
    for method in ("address_dump", "subnet_dump"):
        try:
            result = await mi.call(server, method)
        except mi.MIError as exc:
            logger.warning("%s failed: %s", method, exc)
            return {}, str(exc)
        for partition in (result or {}).get("Partitions", []) if isinstance(result, dict) else []:
            for entry in partition.get("Destinations", []) or []:
                key = _key(entry.get("grp"), entry.get("ip"), entry.get("mask"), entry.get("port"), entry.get("proto"))
                entries[key] = {
                    "partition": partition.get("name"),
                    "grp": entry.get("grp"),
                    "ip": entry.get("ip"),
                    "mask": entry.get("mask"),
                    "port": entry.get("port"),
                    "proto": entry.get("proto"),
                    "pattern": entry.get("pattern") or None,
                    "context_info": entry.get("context_info") or None,
                }
    return entries, None


async def list_addresses(server: OpensipsServer) -> dict[str, Any]:
    """Таблица address, помеченная состоянием в памяти, плюс записи, которых в таблице нет."""
    rows = await table_crud.fetch(server, TABLE, COLUMNS, order_by="grp, ip, id")
    entries, mi_error = await runtime_state(server)

    seen: set[tuple] = set()
    for row in rows:
        key = _key(row["grp"], row["ip"], row["mask"], row["port"], row["proto"])
        seen.add(key)
        runtime = entries.get(key)
        row["in_memory"] = None if mi_error else runtime is not None
        row["partition"] = runtime.get("partition") if runtime else None

    memory_only = [entry for key, entry in entries.items() if key not in seen]
    return {
        "rows": rows,
        "memory_only": memory_only,
        "mi_available": mi_error is None,
        "mi_error": mi_error,
    }


async def reload(server: OpensipsServer, partition: str | None = None) -> Any:
    return await mi.call(server, "address_reload", {"partition": partition} if partition else None)


async def get(server: OpensipsServer, row_id: int) -> dict | None:
    return await table_crud.get(server, TABLE, COLUMNS, row_id)


async def create(server: OpensipsServer, data: dict[str, Any]) -> int | None:
    return await table_crud.insert(server, TABLE, COLUMNS, data)


async def update(server: OpensipsServer, row_id: int, data: dict[str, Any]) -> int:
    return await table_crud.update(server, TABLE, COLUMNS, row_id, data)


async def delete(server: OpensipsServer, row_id: int) -> int:
    return await table_crud.delete(server, TABLE, row_id)
