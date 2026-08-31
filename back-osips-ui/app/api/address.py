"""Таблица address модуля permissions: доверенные адреса и подсети. Права: address:read / address:write."""

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.deps import ClientIP, CurrentUser, ServerDep, SessionDep, require
from ..core.roles import Perm
from ..db.audit import write_audit
from ..schemas.address import AddressReloadIn, AddressRowIn, AddressRowUpdate, AddressTable
from ..schemas.opensips import ActionResult
from ..services import address as addr

router = APIRouter(prefix="/api/servers/{server_id}/address", tags=["address"])

read_only = Depends(require(Perm.ADDRESS_READ))
writable = Depends(require(Perm.ADDRESS_WRITE))


@router.get("", response_model=AddressTable, dependencies=[read_only], summary="Таблица address + дамп из памяти")
async def list_rows(server: ServerDep) -> AddressTable:
    return AddressTable(**await addr.list_addresses(server))


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[writable], summary="Добавить адрес")
async def create_row(payload: AddressRowIn, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    row_id = await addr.create(server, payload.model_dump())
    await write_audit(
        session,
        user=actor,
        action="address.create",
        server=server,
        target=f"{payload.ip}/{payload.mask}",
        details=payload.model_dump(),
        client_ip=ip,
    )
    return {"ok": True, "id": row_id}


@router.put("/{row_id}", dependencies=[writable], summary="Изменить адрес")
async def update_row(
    row_id: int, payload: AddressRowUpdate, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP
) -> dict:
    data = payload.model_dump(exclude_unset=True)
    updated = await addr.update(server, row_id, data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена или изменять нечего")
    await write_audit(session, user=actor, action="address.update", server=server, target=str(row_id), details=data, client_ip=ip)
    return {"ok": True, "updated": updated}


@router.delete("/{row_id}", dependencies=[writable], summary="Удалить адрес")
async def delete_row(row_id: int, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    row = await addr.get(server, row_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена")
    await addr.delete(server, row_id)
    await write_audit(
        session, user=actor, action="address.delete", server=server, target=f"{row.get('ip')}/{row.get('mask')}", details=row, client_ip=ip
    )
    return {"ok": True}


@router.post("/reload", response_model=ActionResult, dependencies=[writable], summary="Обновить в памяти opensips (address_reload)")
async def reload_table(
    server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP, payload: AddressReloadIn | None = None
) -> ActionResult:
    partition = payload.partition if payload else None
    result = await addr.reload(server, partition)
    await write_audit(session, user=actor, action="address.reload", server=server, target=partition, client_ip=ip)
    return ActionResult(detail=result)
