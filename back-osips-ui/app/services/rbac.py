"""Матрица «роль -> права» из БД приложения.

require() дёргается на каждый запрос, поэтому матрица держится в памяти процесса.
У каждого воркера gunicorn кеш свой, синхронизировать их нечем, поэтому кеш живёт
RBAC_CACHE_TTL секунд: правки ролей доезжают до всех воркеров максимум за это время.
В своём процессе изменения видны сразу - api/roles.py зовёт invalidate().
"""

import logging
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..core.roles import ADMIN_ROLE, Perm
from ..db.models import Role, RolePermission

logger = logging.getLogger("osips-ui")

_matrix: dict[str, set[Perm]] = {}
_loaded_at: float = 0.0


def invalidate() -> None:
    global _loaded_at
    _loaded_at = 0.0


async def _load(session: AsyncSession) -> dict[str, set[Perm]]:
    rows = await session.execute(
        select(Role.slug, RolePermission.permission).join(RolePermission, RolePermission.role_id == Role.id, isouter=True)
    )
    matrix: dict[str, set[Perm]] = {}
    for slug, permission in rows:
        granted = matrix.setdefault(slug, set())
        try:
            if permission is not None:
                granted.add(Perm(permission))
        except ValueError:
            # право удалили из кода, а в БД оно осталось - просто игнорируем
            logger.warning("Неизвестное право '%s' у роли '%s'", permission, slug)
    # у встроенного администратора всегда полный доступ, что бы ни лежало в БД
    matrix[ADMIN_ROLE] = set(Perm)
    return matrix


async def matrix(session: AsyncSession) -> dict[str, set[Perm]]:
    global _matrix, _loaded_at
    now = time.monotonic()
    if now - _loaded_at > settings.RBAC_CACHE_TTL:
        _matrix = await _load(session)
        _loaded_at = now
    return _matrix


async def permissions_for(session: AsyncSession, role: str) -> set[Perm]:
    return (await matrix(session)).get(role, set())


async def has_perm(session: AsyncSession, role: str, perm: Perm) -> bool:
    return perm in await permissions_for(session, role)
