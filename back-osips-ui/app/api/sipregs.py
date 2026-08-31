"""SIP-регистрации - таблица location или ul_dump. Только чтение, доступно всем ролям."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..config import settings
from ..core.deps import ServerDep, require
from ..core.roles import Perm
from ..schemas.sipregs import RegistrationOut, RegistrationPage, RegSource
from ..services import mi, opensips_db, sipregs

router = APIRouter(prefix="/api/servers/{server_id}/sip-regs", tags=["sip-regs"])


@router.get("", response_model=RegistrationPage, dependencies=[Depends(require(Perm.SIPREGS_READ))], summary="Список SIP-регистраций")
async def list_registrations(
    server: ServerDep,
    source: RegSource = Query("db", description="db - таблица location, mi - ul_dump из памяти opensips"),
    page: int = Query(1, ge=1),
    per_page: int = Query(settings.SIPREGS_PAGE_SIZE, ge=1, le=200),
    search: str | None = Query(None, description="Подстрока номера, contact, received или user-agent"),
    only_active: bool = Query(False, description="Скрыть истёкшие регистрации"),
) -> RegistrationPage:
    if source == "mi" and not mi.has_mi(server):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Для сервера '{server.name}' не настроен http MI")
    if source == "db" and not opensips_db.has_db(server):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Для сервера '{server.name}' не настроено подключение к БД")

    data = await sipregs.list_contacts(
        server, source=source, page=page, per_page=per_page, search=search, only_active=only_active
    )
    return RegistrationPage(
        source=data["source"],
        items=[RegistrationOut(**item) for item in data["items"]],
        total=data["total"],
        users=data["users"],
        page=data["page"],
        per_page=data["per_page"],
    )
