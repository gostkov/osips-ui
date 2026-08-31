"""Таблица dispatcher: просмотр, редактирование, вывод нод из обслуживания, ds_reload."""

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.deps import ClientIP, CurrentUser, ServerDep, SessionDep, require
from ..core.roles import Perm
from ..db.audit import write_audit
from ..schemas.opensips import ActionResult, DispatcherRowIn, DispatcherRowUpdate, DispatcherStateIn, TableResponse
from ..services import dispatcher as ds

router = APIRouter(prefix="/api/servers/{server_id}/dispatcher", tags=["dispatcher"])

read_only = Depends(require(Perm.DISPATCHER_READ))
writable = Depends(require(Perm.DISPATCHER_WRITE))


@router.get("", response_model=TableResponse, dependencies=[read_only], summary="Таблица dispatcher + состояние нод из ds_list")
async def list_rows(server: ServerDep) -> TableResponse:
    return TableResponse(**await ds.list_destinations(server))


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[writable], summary="Добавить строку")
async def create_row(payload: DispatcherRowIn, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    row_id = await ds.create(server, payload.model_dump())
    await write_audit(
        session, user=actor, action="dispatcher.create", server=server, target=payload.destination, details=payload.model_dump(), client_ip=ip
    )
    return {"ok": True, "id": row_id}


@router.put("/{row_id}", dependencies=[writable], summary="Изменить строку")
async def update_row(
    row_id: int, payload: DispatcherRowUpdate, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP
) -> dict:
    data = payload.model_dump(exclude_unset=True)
    updated = await ds.update(server, row_id, data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Строка не найдена или изменять нечего")
    await write_audit(session, user=actor, action="dispatcher.update", server=server, target=str(row_id), details=data, client_ip=ip)
    return {"ok": True, "updated": updated}


@router.delete("/{row_id}", dependencies=[writable], summary="Удалить строку")
async def delete_row(row_id: int, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    row = await ds.get(server, row_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Строка не найдена")
    await ds.delete(server, row_id)
    await write_audit(
        session, user=actor, action="dispatcher.delete", server=server, target=str(row.get("destination")), details=row, client_ip=ip
    )
    return {"ok": True}


@router.post("/{row_id}/state", response_model=ActionResult, dependencies=[writable], summary="Переключить состояние ноды (ds_set_state)")
async def set_state(
    row_id: int, payload: DispatcherStateIn, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP
) -> ActionResult:
    row = await ds.get(server, row_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Строка не найдена")

    result = await ds.set_state(server, int(row["setid"]), str(row["destination"]), payload.state)
    await write_audit(
        session,
        user=actor,
        action="dispatcher.set_state",
        server=server,
        target=f"{row['setid']}:{row['destination']}",
        details={"state": payload.state},
        client_ip=ip,
    )
    return ActionResult(detail=result)


@router.post("/reload", response_model=ActionResult, dependencies=[writable], summary="Обновить в памяти opensips (ds_reload)")
async def reload_table(server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> ActionResult:
    result = await ds.reload(server)
    await write_audit(session, user=actor, action="dispatcher.reload", server=server, client_ip=ip)
    return ActionResult(detail=result)
