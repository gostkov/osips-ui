"""Журнал действий пользователей."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from ..core.deps import SessionDep, require
from ..core.roles import Perm
from ..db.models import AuditLog

router = APIRouter(prefix="/api/audit", tags=["audit"], dependencies=[Depends(require(Perm.AUDIT_READ))])


@router.get("", summary="Журнал действий")
async def list_audit(
    session: SessionDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    action: str | None = None,
    username: str | None = None,
) -> dict:
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    count_query = select(func.count()).select_from(AuditLog)
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if username:
        query = query.where(AuditLog.username == username)
        count_query = count_query.where(AuditLog.username == username)

    total = await session.scalar(count_query)
    rows = await session.scalars(query.limit(per_page).offset((page - 1) * per_page))
    items = [
        {
            "id": row.id,
            "created_at": row.created_at,
            "username": row.username,
            "role": row.role,
            "action": row.action,
            "server_name": row.server_name,
            "target": row.target,
            "details": row.details,
            "success": row.success,
            "client_ip": row.client_ip,
        }
        for row in rows
    ]
    return {"items": items, "total": total or 0, "page": page, "per_page": per_page}
