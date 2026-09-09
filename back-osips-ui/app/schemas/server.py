from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ServerBase(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    ip_address: str = Field(min_length=1, max_length=64)

    mi_host: str | None = Field(default=None, max_length=64)
    mi_port: int | None = Field(default=None, ge=1, le=65535)
    mi_path: str = "/mi"
    mi_username: str | None = Field(default=None, max_length=64)

    db_host: str | None = Field(default=None, max_length=128)
    db_port: int = Field(default=3306, ge=1, le=65535)
    db_name: str | None = Field(default=None, max_length=64)
    db_user: str | None = Field(default=None, max_length=64)

    dispatcher_partition: str = "default"
    is_active: bool = True
    sort_order: int = 100


class ServerCreate(ServerBase):
    mi_password: str | None = None
    db_password: str | None = None


class ServerUpdate(BaseModel):
    """Все поля опциональны. Пустая строка в пароле = очистить, None = оставить прежний."""

    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = None
    ip_address: str | None = None
    mi_host: str | None = None
    mi_port: int | None = Field(default=None, ge=1, le=65535)
    mi_path: str | None = None
    mi_username: str | None = None
    mi_password: str | None = None
    db_host: str | None = None
    db_port: int | None = Field(default=None, ge=1, le=65535)
    db_name: str | None = None
    db_user: str | None = None
    db_password: str | None = None
    dispatcher_partition: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class ServerOut(BaseModel):
    """Карточка сервера.

    Селектор серверов нужен на каждой странице, поэтому список видит любой
    аутентифицированный пользователь - но реквизиты инфраструктуры (адреса, имена БД
    и учётные записи) приезжают только тем, у кого есть servers:read. Остальным
    приходит null, см. to_out() в api/servers.py.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_active: bool = True
    sort_order: int = 100
    has_db: bool = False
    has_mi: bool = False

    description: str | None = None
    ip_address: str | None = None
    mi_host: str | None = None
    mi_port: int | None = None
    mi_path: str | None = None
    mi_username: str | None = None
    db_host: str | None = None
    db_port: int | None = None
    db_name: str | None = None
    db_user: str | None = None
    dispatcher_partition: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ServerCheck(BaseModel):
    ok: bool
    detail: str | None = None


class ServerCheckOut(BaseModel):
    db: ServerCheck
    mi: ServerCheck
