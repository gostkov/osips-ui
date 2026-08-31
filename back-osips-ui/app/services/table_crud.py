"""Однотипный SQL для таблиц opensips: выборка с пагинацией и CRUD по id.

dialplan, rtpengine, userblacklist/globalblacklist и address устроены одинаково - таблица
с автоинкрементным id, которую opensips перечитывает по MI-команде. Отличаются они только
именем таблицы и набором колонок, поэтому запросы собираются здесь, а не копируются
в каждый сервис.

Имена таблиц и колонок берутся из констант сервисов; всё, что пришло от пользователя,
подставляется только bind-параметрами.
"""

from typing import Any, Sequence

from ..db.models import OpensipsServer
from . import opensips_db


def _select_list(columns: Sequence[str]) -> str:
    return "id, " + ", ".join(columns)


def _where(clause: str) -> str:
    return f" WHERE {clause}" if clause else ""


async def fetch(
    server: OpensipsServer,
    table: str,
    columns: Sequence[str],
    *,
    where: str = "",
    params: dict[str, Any] | None = None,
    order_by: str = "id",
) -> list[dict]:
    """Вся таблица целиком - для небольших справочников (rtpengine, address)."""
    return await opensips_db.fetch_all(
        server,
        f"SELECT {_select_list(columns)} FROM {table}{_where(where)} ORDER BY {order_by}",
        params or {},
    )


async def fetch_page(
    server: OpensipsServer,
    table: str,
    columns: Sequence[str],
    *,
    where: str = "",
    params: dict[str, Any] | None = None,
    order_by: str = "id",
    page: int = 1,
    per_page: int = 25,
) -> dict[str, Any]:
    """Страница таблицы - для тех, где строк могут быть тысячи (dialplan, списки номеров)."""
    params = params or {}
    offset = (max(page, 1) - 1) * per_page
    total = (await opensips_db.fetch_all(server, f"SELECT COUNT(*) AS cnt FROM {table}{_where(where)}", params))[0]["cnt"]
    rows = await opensips_db.fetch_all(
        server,
        f"SELECT {_select_list(columns)} FROM {table}{_where(where)} ORDER BY {order_by} LIMIT :limit OFFSET :offset",
        params | {"limit": per_page, "offset": offset},
    )
    return {"items": rows, "total": int(total), "page": page, "per_page": per_page}


async def get(server: OpensipsServer, table: str, columns: Sequence[str], row_id: int) -> dict | None:
    rows = await opensips_db.fetch_all(
        server,
        f"SELECT {_select_list(columns)} FROM {table} WHERE id = :id",
        {"id": row_id},
    )
    return rows[0] if rows else None


async def insert(server: OpensipsServer, table: str, columns: Sequence[str], data: dict[str, Any]) -> int | None:
    fields = [column for column in columns if column in data]
    sql = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({', '.join(':' + field for field in fields)})"
    result = await opensips_db.execute(server, sql, {field: data[field] for field in fields})
    return result["lastrowid"]


async def update(server: OpensipsServer, table: str, columns: Sequence[str], row_id: int, data: dict[str, Any]) -> int:
    fields = [column for column in columns if column in data]
    if not fields:
        return 0
    sql = f"UPDATE {table} SET {', '.join(f'{field} = :{field}' for field in fields)} WHERE id = :id"
    result = await opensips_db.execute(server, sql, {field: data[field] for field in fields} | {"id": row_id})
    return result["rowcount"]


async def delete(server: OpensipsServer, table: str, row_id: int) -> int:
    result = await opensips_db.execute(server, f"DELETE FROM {table} WHERE id = :id", {"id": row_id})
    return result["rowcount"]
