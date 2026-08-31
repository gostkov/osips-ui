"""Таблица rtpengine: сокеты, их состояние в памяти, rtpengine_enable и rtpengine_reload.

Права: rtpengine:read / rtpengine:write.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.deps import ClientIP, CurrentUser, ServerDep, SessionDep, require
from ..core.roles import Perm
from ..db.audit import write_audit
from ..schemas.opensips import ActionResult, TableResponse
from ..schemas.rtpengine import RtpengineEnableIn, RtpengineReloadIn, RtpengineRowIn, RtpengineRowUpdate
from ..services import rtpengine as rtpe

router = APIRouter(prefix="/api/servers/{server_id}/rtpengine", tags=["rtpengine"])

read_only = Depends(require(Perm.RTPENGINE_READ))
writable = Depends(require(Perm.RTPENGINE_WRITE))


@router.get("", response_model=TableResponse, dependencies=[read_only], summary="Таблица rtpengine + состояние из rtpengine_show")
async def list_rows(server: ServerDep) -> TableResponse:
    return TableResponse(**await rtpe.list_sockets(server))


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[writable], summary="Добавить сокет")
async def create_row(payload: RtpengineRowIn, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    row_id = await rtpe.create(server, payload.model_dump())
    await write_audit(
        session, user=actor, action="rtpengine.create", server=server, target=payload.socket, details=payload.model_dump(), client_ip=ip
    )
    return {"ok": True, "id": row_id}


@router.put("/{row_id}", dependencies=[writable], summary="Изменить сокет")
async def update_row(
    row_id: int, payload: RtpengineRowUpdate, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP
) -> dict:
    data = payload.model_dump(exclude_unset=True)
    updated = await rtpe.update(server, row_id, data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Строка не найдена или изменять нечего")
    await write_audit(session, user=actor, action="rtpengine.update", server=server, target=str(row_id), details=data, client_ip=ip)
    return {"ok": True, "updated": updated}


@router.delete("/{row_id}", dependencies=[writable], summary="Удалить сокет")
async def delete_row(row_id: int, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    row = await rtpe.get(server, row_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Строка не найдена")
    await rtpe.delete(server, row_id)
    await write_audit(session, user=actor, action="rtpengine.delete", server=server, target=str(row.get("socket")), details=row, client_ip=ip)
    return {"ok": True}


@router.post("/{row_id}/enabled", response_model=ActionResult, dependencies=[writable], summary="Включить/выключить сокет (rtpengine_enable)")
async def set_enabled(
    row_id: int, payload: RtpengineEnableIn, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP
) -> ActionResult:
    row = await rtpe.get(server, row_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Строка не найдена")

    result = await rtpe.set_enabled(server, int(row["set_id"]), str(row["socket"]), payload.enabled)
    await write_audit(
        session,
        user=actor,
        action="rtpengine.set_enabled",
        server=server,
        target=f"{row['set_id']}:{row['socket']}",
        details={"enabled": payload.enabled},
        client_ip=ip,
    )
    return ActionResult(detail=result)


@router.post("/reload", response_model=ActionResult, dependencies=[writable], summary="Обновить в памяти opensips (rtpengine_reload)")
async def reload_table(
    server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP, payload: RtpengineReloadIn | None = None
) -> ActionResult:
    soft = bool(payload and payload.soft)
    result = await rtpe.reload(server, soft=soft)
    await write_audit(session, user=actor, action="rtpengine.reload", server=server, details={"soft": soft}, client_ip=ip)
    return ActionResult(detail=result)
