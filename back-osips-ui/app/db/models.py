"""Модели БД приложения (SQLite). К схеме opensips отношения не имеют."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(128))
    email: Mapped[str | None] = mapped_column(String(128))
    # password_hash пустой у пользователей, заведённых через SSO
    password_hash: Mapped[str | None] = mapped_column(String(128))
    # slug роли из таблицы roles; связь по строке, чтобы удаление роли не рушило пользователей
    role: Mapped[str] = mapped_column(String(32), default="reader", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # задел под SSO: local | oidc
    auth_provider: Mapped[str] = mapped_column(String(32), default="local", nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)


class Role(Base):
    """Роль: именованный набор прав. Настраивается в интерфейсе."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    # встроенная роль admin: полный доступ, не редактируется и не удаляется
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="role", cascade="all, delete-orphan", lazy="selectin"
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission", name="role_permission_idx"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), index=True, nullable=False)
    permission: Mapped[str] = mapped_column(String(64), nullable=False)

    role: Mapped[Role] = relationship(back_populates="permissions")


class OpensipsServer(Base):
    """Реестр управляемых opensips-серверов.

    Несколько серверов могут ссылаться на одну и ту же БД - тогда поля db_* совпадают.
    """

    __tablename__ = "opensips_servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)

    # http MI (модуль mi_http), например 127.0.0.1:8888 -> http://127.0.0.1:8888/mi
    mi_host: Mapped[str | None] = mapped_column(String(64))
    mi_port: Mapped[int | None] = mapped_column(Integer)
    mi_path: Mapped[str] = mapped_column(String(64), default="/mi", nullable=False)
    mi_username: Mapped[str | None] = mapped_column(String(64))
    mi_password: Mapped[str | None] = mapped_column(String(255))  # хранится в зашифрованном виде

    # БД opensips
    db_host: Mapped[str | None] = mapped_column(String(128))
    db_port: Mapped[int] = mapped_column(Integer, default=3306, nullable=False)
    db_name: Mapped[str | None] = mapped_column(String(64))
    db_user: Mapped[str | None] = mapped_column(String(64))
    db_password: Mapped[str | None] = mapped_column(String(255))  # хранится в зашифрованном виде

    # партиция модуля dispatcher (для ds_list/ds_reload/ds_set_state)
    dispatcher_partition: Mapped[str] = mapped_column(String(64), default="default", nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class AuditLog(Base):
    """Журнал действий, меняющих состояние opensips или пользователей."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    server_id: Mapped[int | None] = mapped_column(Integer, index=True)
    server_name: Mapped[str | None] = mapped_column(String(64))
    target: Mapped[str | None] = mapped_column(String(255))
    details: Mapped[str | None] = mapped_column(Text)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    client_ip: Mapped[str | None] = mapped_column(String(64))
