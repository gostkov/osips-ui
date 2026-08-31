"""Списки номеров: userblacklist (правила на абонента) и globalblacklist (общие префиксы).

Права: blacklist:read / blacklist:write.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..config import settings
from ..core.deps import ClientIP, CurrentUser, ServerDep, SessionDep, require
from ..core.roles import Perm
from ..db.audit import write_audit
from ..db.models import OpensipsServer, User
from ..schemas.blacklist import (
    BlacklistPage,
    GlobalBlacklistIn,
    GlobalBlacklistUpdate,
    UserBlacklistIn,
    UserBlacklistUpdate,
)
from ..schemas.opensips import ActionResult
from ..services import blacklist as bl

router = APIRouter(prefix="/api/servers/{server_id}/blacklist", tags=["blacklist"])

read_only = Depends(require(Perm.BLACKLIST_READ))
writable = Depends(require(Perm.BLACKLIST_WRITE))


def _target(kind: str, row: dict[str, Any]) -> str:
    """Что писать в журнал: для userblacklist номер уточняется абонентом."""
    prefix = str(row.get("prefix") or "")
    if kind == "user" and row.get("username"):
        return f"{row.get('username')}@{row.get('domain') or ''}:{prefix}"
    return prefix


async def _create(kind: str, data: dict, server: OpensipsServer, session, actor: User, ip: str | None) -> dict:
    row_id = await bl.create(server, kind, data)
    await write_audit(session, user=actor, action=f"blacklist.{kind}.create", server=server, target=_target(kind, data), details=data, client_ip=ip)
    return {"ok": True, "id": row_id}


async def _update(kind: str, row_id: int, data: dict, server: OpensipsServer, session, actor: User, ip: str | None) -> dict:
    updated = await bl.update(server, kind, row_id, data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена или изменять нечего")
    await write_audit(session, user=actor, action=f"blacklist.{kind}.update", server=server, target=str(row_id), details=data, client_ip=ip)
    return {"ok": True, "updated": updated}


async def _delete(kind: str, row_id: int, server: OpensipsServer, session, actor: User, ip: str | None) -> dict:
    row = await bl.get(server, kind, row_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена")
    await bl.delete(server, kind, row_id)
    await write_audit(session, user=actor, action=f"blacklist.{kind}.delete", server=server, target=_target(kind, row), details=row, client_ip=ip)
    return {"ok": True}


@router.get("/user", response_model=BlacklistPage, dependencies=[read_only], summary="Таблица userblacklist")
async def list_user_entries(
    server: ServerDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(settings.BLACKLIST_PAGE_SIZE, ge=1, le=200),
    search: str | None = Query(None, description="Подстрока в username / domain / prefix"),
    only: str | None = Query(None, pattern="^(black|white)$", description="Только запрещающие или только разрешающие правила"),
) -> BlacklistPage:
    return BlacklistPage(**await bl.list_entries(server, "user", page=page, per_page=per_page, search=search, only=only))


@router.post("/user", status_code=status.HTTP_201_CREATED, dependencies=[writable], summary="Добавить правило userblacklist")
async def create_user_entry(payload: UserBlacklistIn, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    return await _create("user", payload.model_dump(), server, session, actor, ip)


@router.put("/user/{row_id}", dependencies=[writable], summary="Изменить правило userblacklist")
async def update_user_entry(
    row_id: int, payload: UserBlacklistUpdate, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP
) -> dict:
    return await _update("user", row_id, payload.model_dump(exclude_unset=True), server, session, actor, ip)


@router.delete("/user/{row_id}", dependencies=[writable], summary="Удалить правило userblacklist")
async def delete_user_entry(row_id: int, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    return await _delete("user", row_id, server, session, actor, ip)


@router.get("/global", response_model=BlacklistPage, dependencies=[read_only], summary="Таблица globalblacklist")
async def list_global_entries(
    server: ServerDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(settings.BLACKLIST_PAGE_SIZE, ge=1, le=200),
    search: str | None = Query(None, description="Подстрока в prefix / description"),
    only: str | None = Query(None, pattern="^(black|white)$", description="Только запрещающие или только разрешающие правила"),
) -> BlacklistPage:
    return BlacklistPage(**await bl.list_entries(server, "global", page=page, per_page=per_page, search=search, only=only))


@router.post("/global", status_code=status.HTTP_201_CREATED, dependencies=[writable], summary="Добавить правило globalblacklist")
async def create_global_entry(payload: GlobalBlacklistIn, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    return await _create("global", payload.model_dump(), server, session, actor, ip)


@router.put("/global/{row_id}", dependencies=[writable], summary="Изменить правило globalblacklist")
async def update_global_entry(
    row_id: int, payload: GlobalBlacklistUpdate, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP
) -> dict:
    return await _update("global", row_id, payload.model_dump(exclude_unset=True), server, session, actor, ip)


@router.delete("/global/{row_id}", dependencies=[writable], summary="Удалить правило globalblacklist")
async def delete_global_entry(row_id: int, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    return await _delete("global", row_id, server, session, actor, ip)


@router.post("/reload", response_model=ActionResult, dependencies=[writable], summary="Обновить в памяти opensips (reload_blacklist)")
async def reload_lists(server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> ActionResult:
    result = await bl.reload(server)
    await write_audit(session, user=actor, action="blacklist.reload", server=server, client_ip=ip)
    return ActionResult(detail=result)
