"""Подключение к БД приложения (SQLite) и bootstrap первого администратора."""

import fcntl
import logging
from collections.abc import AsyncGenerator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..config import DEFAULT_ADMIN_PASSWORD, settings
from ..core.roles import ADMIN_ROLE, DEFAULT_ROLES
from ..core.security import hash_password
from .models import Base, Role, RolePermission, User

logger = logging.getLogger("osips-ui")

_db_path = Path(settings.APP_DB_PATH)
_db_path.parent.mkdir(parents=True, exist_ok=True)

# timeout: при параллельной записи ждать снятия блокировки, а не падать сразу на "database is locked"
engine = create_async_engine(
    f"sqlite+aiosqlite:///{_db_path}",
    echo=settings.DEBUG,
    future=True,
    connect_args={"timeout": settings.APP_DB_TIMEOUT},
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


_init_lock_path = _db_path.with_name(_db_path.name + ".init.lock")


@contextmanager
def _init_lock():
    """Межпроцессная блокировка инициализации.

    Воркеры gunicorn стартуют одновременно, и на пустой базе они наперегонки выполняют
    create_all и первичное наполнение. Проигравший получал "database is locked" на
    PRAGMA journal_mode=WAL и падал, а gunicorn на упавшем воркере гасил всю службу.
    Блокировка пропускает воркеры по одному; второму и следующим остаётся no-op.
    """
    with open(_init_lock_path, "w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


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
    with _init_lock():
        await _init_db()


async def _init_db() -> None:
    async with engine.begin() as conn:
        # WAL заметно снижает шанс "database is locked" при нескольких воркерах
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        await _seed_roles(session)

        exists = await session.scalar(select(User.id).limit(1))
        if exists:
            return
        if not settings.DEBUG and settings.BOOTSTRAP_ADMIN_PASSWORD == DEFAULT_ADMIN_PASSWORD:
            # создать первого админа с паролем admin/admin - всё равно что не заводить пароль вовсе
            raise RuntimeError(
                "BOOTSTRAP_ADMIN_PASSWORD остался значением по умолчанию ('admin'), "
                "а таблица пользователей пуста. Задайте пароль первого администратора в .env и перезапустите."
            )
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
