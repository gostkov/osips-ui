"""Подключение к БД приложения (SQLite) и bootstrap первого администратора."""

import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..config import settings
from ..core.roles import ADMIN_ROLE, DEFAULT_ROLES
from ..core.security import hash_password
from .models import Base, Role, RolePermission, User

logger = logging.getLogger("osips-ui")

_db_path = Path(settings.APP_DB_PATH)
_db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(f"sqlite+aiosqlite:///{_db_path}", echo=settings.DEBUG, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def _seed_roles(session) -> None:
    """Создаёт роли по умолчанию, если таблица пустая. Дальше роли живут своей жизнью."""
    if await session.scalar(select(Role.id).limit(1)):
        return
    for spec in DEFAULT_ROLES:
        session.add(
            Role(
                slug=spec["slug"],
                title=spec["title"],
                description=spec["description"],
                is_builtin=spec["is_builtin"],
                permissions=[RolePermission(permission=perm.value) for perm in spec["permissions"]],
            )
        )
    await session.commit()
    logger.info("Созданы роли по умолчанию: %s", ", ".join(spec["slug"] for spec in DEFAULT_ROLES))


async def init_db() -> None:
    async with engine.begin() as conn:
        # WAL заметно снижает шанс "database is locked" при нескольких воркерах
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        await _seed_roles(session)

        exists = await session.scalar(select(User.id).limit(1))
        if exists:
            return
        admin = User(
            username=settings.BOOTSTRAP_ADMIN_USERNAME,
            full_name="Bootstrap administrator",
            password_hash=hash_password(settings.BOOTSTRAP_ADMIN_PASSWORD),
            role=ADMIN_ROLE,
        )
        session.add(admin)
        await session.commit()
        logger.warning(
            "Создан первый пользователь '%s' с ролью %s. Смените пароль сразу после входа.",
            settings.BOOTSTRAP_ADMIN_USERNAME,
            ADMIN_ROLE,
        )
