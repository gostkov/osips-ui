"""Доступ к БД opensips (MySQL/MariaDB).

У каждого сервера из реестра свои реквизиты БД, поэтому движки SQLAlchemy кешируются
по набору реквизитов: серверы с общей БД переиспользуют один пул.
"""

import logging
from typing import Any

from sqlalchemy import URL, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from ..config import settings
from ..core.crypto import decrypt
from ..db.models import OpensipsServer

logger = logging.getLogger("osips-ui")

_engines: dict[tuple, AsyncEngine] = {}


class OpensipsDBError(RuntimeError):
    pass


def has_db(server: OpensipsServer) -> bool:
    return bool(server.db_host and server.db_name and server.db_user)


def _key(server: OpensipsServer) -> tuple:
    return (server.db_host, server.db_port, server.db_name, server.db_user, decrypt(server.db_password) or "")


def get_engine(server: OpensipsServer) -> AsyncEngine:
    if not has_db(server):
        raise OpensipsDBError(f"Для сервера '{server.name}' не настроено подключение к БД")
    key = _key(server)
    engine = _engines.get(key)
    if engine is None:
        url = URL.create(
            "mysql+aiomysql",
            username=key[3],
            password=key[4],
            host=key[0],
            port=key[1] or 3306,
            database=key[2],
        )
        engine = create_async_engine(
            url,
            pool_size=settings.OPENSIPS_DB_POOL_SIZE,
            max_overflow=settings.OPENSIPS_DB_POOL_MAX_OVERFLOW,
            pool_recycle=1700,
            pool_pre_ping=True,
            connect_args={"connect_timeout": settings.OPENSIPS_DB_CONNECT_TIMEOUT},
        )
        _engines[key] = engine
        logger.info("Создан пул подключений к БД opensips %s:%s/%s", key[0], key[1], key[2])
    return engine


async def dispose_for(server: OpensipsServer) -> None:
    """Закрывает пул для текущих реквизитов сервера (вызывается при их изменении/удалении)."""
    if not has_db(server):
        return
    engine = _engines.pop(_key(server), None)
    if engine is not None:
        await engine.dispose()


async def dispose_all() -> None:
    for engine in list(_engines.values()):
        await engine.dispose()
    _engines.clear()


async def fetch_all(server: OpensipsServer, sql: str, params: dict[str, Any] | None = None) -> list[dict]:
    engine = get_engine(server)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(sql), params or {})
            return [dict(row) for row in result.mappings().all()]
    except SQLAlchemyError as exc:
        raise OpensipsDBError(f"{server.name}: ошибка запроса к БД: {exc.__class__.__name__}: {exc}") from exc


async def execute(server: OpensipsServer, sql: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    engine = get_engine(server)
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text(sql), params or {})
            return {"rowcount": result.rowcount, "lastrowid": getattr(result, "lastrowid", None)}
    except SQLAlchemyError as exc:
        raise OpensipsDBError(f"{server.name}: ошибка записи в БД: {exc.__class__.__name__}: {exc}") from exc


async def ping(server: OpensipsServer) -> dict[str, Any]:
    try:
        await fetch_all(server, "SELECT 1 AS ok")
        return {"ok": True, "detail": "подключение установлено"}
    except (OpensipsDBError, OSError) as exc:
        return {"ok": False, "detail": str(exc)}
