"""Реестр opensips-серверов. Права: servers:read / servers:write."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from ..core.crypto import encrypt
from ..core.deps import ClientIP, CurrentUser, ServerDep, SessionDep, require
from ..core.roles import Perm
from ..db.audit import write_audit
from ..db.models import OpensipsServer
from ..schemas.server import ServerCheck, ServerCheckOut, ServerCreate, ServerOut, ServerUpdate
from ..services import mi, opensips_db, rbac

router = APIRouter(prefix="/api/servers", tags=["servers"])

SECRET_FIELDS = ("mi_password", "db_password")


def to_out(server: OpensipsServer, *, full: bool = True) -> ServerOut:
    """full=False - только то, что нужно селектору серверов, без реквизитов инфраструктуры."""
    out = ServerOut.model_validate(server, from_attributes=True).model_copy(
        update={
            "has_db": opensips_db.has_db(server),
            "has_mi": mi.has_mi(server),
        }
    )
    if full:
        return out
    return ServerOut(
        id=out.id,
        name=out.name,
        is_active=out.is_active,
        sort_order=out.sort_order,
        has_db=out.has_db,
        has_mi=out.has_mi,
    )


@router.get("", response_model=list[ServerOut], summary="Список серверов")
async def list_servers(session: SessionDep, user: CurrentUser, only_active: bool = False) -> list[ServerOut]:
    """Без права servers:read отдаётся сокращённая карточка: id, имя, статус, признаки БД и MI."""
    full = await rbac.has_perm(session, user.role, Perm.SERVERS_READ)
    query = select(OpensipsServer).order_by(OpensipsServer.sort_order, OpensipsServer.name)
    if only_active:
        query = query.where(OpensipsServer.is_active.is_(True))
    return [to_out(server, full=full) for server in await session.scalars(query)]


@router.get(
    "/{server_id}",
    response_model=ServerOut,
    summary="Карточка сервера",
    dependencies=[Depends(require(Perm.SERVERS_READ))],
)
async def get_server_detail(server: ServerDep) -> ServerOut:
    return to_out(server)


@router.post("", response_model=ServerOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require(Perm.SERVERS_WRITE))])
async def create_server(payload: ServerCreate, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> ServerOut:
    exists = await session.scalar(select(OpensipsServer.id).where(OpensipsServer.name == payload.name))
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Сервер с таким именем уже есть")

    data = payload.model_dump()
    for field in SECRET_FIELDS:
        data[field] = encrypt(data.get(field))
    server = OpensipsServer(**data)
    session.add(server)
    await session.commit()
    await write_audit(session, user=actor, action="servers.create", server=server, client_ip=ip)
    return to_out(server)


@router.put("/{server_id}", response_model=ServerOut, dependencies=[Depends(require(Perm.SERVERS_WRITE))])
async def update_server(payload: ServerUpdate, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> ServerOut:
    data = payload.model_dump(exclude_unset=True)
    await opensips_db.dispose_for(server)

    for field, value in data.items():
        if field in SECRET_FIELDS:
            # пустая строка = очистить секрет, отсутствие поля = оставить как было
            setattr(server, field, encrypt(value) if value else None)
        else:
            setattr(server, field, value)
    await session.commit()
    await write_audit(
        session,
        user=actor,
        action="servers.update",
        server=server,
        details={key: ("***" if key in SECRET_FIELDS else value) for key, value in data.items()},
        client_ip=ip,
    )
    return to_out(server)


@router.delete("/{server_id}", dependencies=[Depends(require(Perm.SERVERS_WRITE))])
async def delete_server(server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    await opensips_db.dispose_for(server)
    name = server.name
    await session.delete(server)
    await session.commit()
    await write_audit(session, user=actor, action="servers.delete", target=name, client_ip=ip)
    return {"ok": True}


@router.post(
    "/{server_id}/check",
    response_model=ServerCheckOut,
    summary="Проверка доступности БД и http MI",
    dependencies=[Depends(require(Perm.SERVERS_READ))],
)
async def check_server(server: ServerDep) -> ServerCheckOut:
    db_result = (
        await opensips_db.ping(server) if opensips_db.has_db(server) else {"ok": False, "detail": "подключение к БД не настроено"}
    )
    mi_result = await mi.ping(server) if mi.has_mi(server) else {"ok": False, "detail": "http MI не настроен"}
    return ServerCheckOut(db=ServerCheck(**db_result), mi=ServerCheck(**mi_result))
