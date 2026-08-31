"""Запись в журнал действий."""

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditLog, OpensipsServer, User

logger = logging.getLogger("osips-ui")


async def write_audit(
    session: AsyncSession,
    *,
    user: User,
    action: str,
    server: OpensipsServer | None = None,
    target: str | None = None,
    details: dict | None = None,
    success: bool = True,
    client_ip: str | None = None,
) -> None:
    entry = AuditLog(
        username=user.username,
        role=user.role,
        action=action,
        server_id=server.id if server else None,
        server_name=server.name if server else None,
        target=target,
        details=json.dumps(details, ensure_ascii=False, default=str) if details else None,
        success=success,
        client_ip=client_ip,
    )
    session.add(entry)
    await session.commit()
    logger.info("audit: user=%s action=%s server=%s target=%s ok=%s", user.username, action, entry.server_name, target, success)
