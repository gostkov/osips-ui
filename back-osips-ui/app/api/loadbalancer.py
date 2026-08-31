"""Таблица load_balancer: просмотр, редактирование, включение/выключение назначений, lb_reload."""

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.deps import ClientIP, CurrentUser, ServerDep, SessionDep, require
from ..core.roles import Perm
from ..db.audit import write_audit
from ..schemas.opensips import ActionResult, LoadBalancerRowIn, LoadBalancerRowUpdate, LoadBalancerStatusIn, TableResponse
from ..services import loadbalancer as lb

router = APIRouter(prefix="/api/servers/{server_id}/loadbalancer", tags=["loadbalancer"])

read_only = Depends(require(Perm.LB_READ))
writable = Depends(require(Perm.LB_WRITE))


@router.get("", response_model=TableResponse, dependencies=[read_only], summary="Таблица load_balancer + состояние из lb_list")
async def list_rows(server: ServerDep) -> TableResponse:
    return TableResponse(**await lb.list_destinations(server))


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[writable], summary="Добавить строку")
async def create_row(payload: LoadBalancerRowIn, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    row_id = await lb.create(server, payload.model_dump())
    await write_audit(
        session, user=actor, action="loadbalancer.create", server=server, target=payload.dst_uri, details=payload.model_dump(), client_ip=ip
    )
    return {"ok": True, "id": row_id}


@router.put("/{row_id}", dependencies=[writable], summary="Изменить строку")
async def update_row(
    row_id: int, payload: LoadBalancerRowUpdate, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP
) -> dict:
    data = payload.model_dump(exclude_unset=True)
    updated = await lb.update(server, row_id, data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Строка не найдена или изменять нечего")
    await write_audit(session, user=actor, action="loadbalancer.update", server=server, target=str(row_id), details=data, client_ip=ip)
    return {"ok": True, "updated": updated}


@router.delete("/{row_id}", dependencies=[writable], summary="Удалить строку")
async def delete_row(row_id: int, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    row = await lb.get(server, row_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Строка не найдена")
    await lb.delete(server, row_id)
    await write_audit(
        session, user=actor, action="loadbalancer.delete", server=server, target=str(row.get("dst_uri")), details=row, client_ip=ip
    )
    return {"ok": True}


@router.post("/{row_id}/status", response_model=ActionResult, dependencies=[writable], summary="Включить/выключить назначение (lb_status)")
async def set_status(
    row_id: int, payload: LoadBalancerStatusIn, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP
) -> ActionResult:
    row = await lb.get(server, row_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Строка не найдена")

    result = await lb.set_status(server, row_id, payload.enabled)
    await write_audit(
        session,
        user=actor,
        action="loadbalancer.set_status",
        server=server,
        target=str(row.get("dst_uri")),
        details={"enabled": payload.enabled},
        client_ip=ip,
    )
    return ActionResult(detail=result)


@router.post("/reload", response_model=ActionResult, dependencies=[writable], summary="Обновить в памяти opensips (lb_reload)")
async def reload_table(server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> ActionResult:
    result = await lb.reload(server)
    await write_audit(session, user=actor, action="loadbalancer.reload", server=server, client_ip=ip)
    return ActionResult(detail=result)
