"""Таблица dialplan: правила трансляции, dp_reload и dp_translate. Права: dialplan:read / dialplan:write."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..config import settings
from ..core.deps import ClientIP, CurrentUser, ServerDep, SessionDep, require
from ..core.roles import Perm
from ..db.audit import write_audit
from ..schemas.dialplan import (
    DialplanDpid,
    DialplanPage,
    DialplanPartitions,
    DialplanRuleIn,
    DialplanRuleOut,
    DialplanRuleUpdate,
    TranslateIn,
    TranslateOut,
)
from ..schemas.opensips import ActionResult
from ..services import dialplan as dp

router = APIRouter(prefix="/api/servers/{server_id}/dialplan", tags=["dialplan"])

read_only = Depends(require(Perm.DIALPLAN_READ))
writable = Depends(require(Perm.DIALPLAN_WRITE))


@router.get("", response_model=DialplanPage, dependencies=[read_only], summary="Правила dialplan с пагинацией")
async def list_rules(
    server: ServerDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(settings.DIALPLAN_PAGE_SIZE, ge=1, le=200),
    search: str | None = Query(None, description="Подстрока в match_exp / subst_exp / repl_exp / attrs"),
    dpid: int | None = Query(None, ge=0, description="Только правила этого набора"),
    only_enabled: bool = Query(False, description="Скрыть правила с disabled=1"),
) -> DialplanPage:
    data = await dp.list_rules(server, page=page, per_page=per_page, search=search, dpid=dpid, only_enabled=only_enabled)
    return DialplanPage(items=[DialplanRuleOut(**row) for row in data["items"]], **{k: data[k] for k in ("total", "page", "per_page")})


@router.get("/dpids", response_model=list[DialplanDpid], dependencies=[read_only], summary="Наборы правил (dpid)")
async def list_dpids(server: ServerDep) -> list[DialplanDpid]:
    return [DialplanDpid(dpid=row["dpid"], rules=int(row["rules"] or 0), enabled=int(row["enabled"] or 0)) for row in await dp.dpids(server)]


@router.get("/partitions", response_model=DialplanPartitions, dependencies=[read_only], summary="Партиции из памяти (dp_show_partition)")
async def list_partitions(server: ServerDep) -> DialplanPartitions:
    items, error = await dp.partitions(server)
    return DialplanPartitions(items=items, mi_available=error is None, mi_error=error)


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[writable], summary="Добавить правило")
async def create_rule(payload: DialplanRuleIn, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    row_id = await dp.create(server, payload.model_dump())
    await write_audit(
        session,
        user=actor,
        action="dialplan.create",
        server=server,
        target=f"{payload.dpid}:{payload.match_exp}",
        details=payload.model_dump(),
        client_ip=ip,
    )
    return {"ok": True, "id": row_id}


@router.put("/{row_id}", dependencies=[writable], summary="Изменить правило")
async def update_rule(
    row_id: int, payload: DialplanRuleUpdate, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP
) -> dict:
    data = payload.model_dump(exclude_unset=True)
    updated = await dp.update(server, row_id, data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Правило не найдено или изменять нечего")
    await write_audit(session, user=actor, action="dialplan.update", server=server, target=str(row_id), details=data, client_ip=ip)
    return {"ok": True, "updated": updated}


@router.delete("/{row_id}", dependencies=[writable], summary="Удалить правило")
async def delete_rule(row_id: int, server: ServerDep, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    row = await dp.get(server, row_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Правило не найдено")
    await dp.delete(server, row_id)
    await write_audit(
        session,
        user=actor,
        action="dialplan.delete",
        server=server,
        target=f"{row.get('dpid')}:{row.get('match_exp')}",
        details=row,
        client_ip=ip,
    )
    return {"ok": True}


@router.post("/reload", response_model=ActionResult, dependencies=[writable], summary="Обновить в памяти opensips (dp_reload)")
async def reload_rules(
    server: ServerDep,
    session: SessionDep,
    actor: CurrentUser,
    ip: ClientIP,
    partition: str | None = Query(None, description="По умолчанию перечитываются все партиции"),
) -> ActionResult:
    result = await dp.reload(server, partition)
    await write_audit(session, user=actor, action="dialplan.reload", server=server, target=partition, client_ip=ip)
    return ActionResult(detail=result)


@router.post("/translate", response_model=TranslateOut, dependencies=[read_only], summary="Прогнать строку через правила (dp_translate)")
async def translate(payload: TranslateIn, server: ServerDep) -> TranslateOut:
    return TranslateOut(**await dp.translate(server, payload.dpid, payload.value, payload.partition))
