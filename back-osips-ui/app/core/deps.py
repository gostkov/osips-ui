"""Зависимости FastAPI: текущий пользователь, проверка прав, выбор сервера."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import OpensipsServer, User
from ..db.session import get_session
from ..services import rbac
from .roles import Perm
from .security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учётные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise credentials_error from exc

    username = payload.get("sub")
    if not username:
        raise credentials_error

    user = await session.scalar(select(User).where(User.username == username))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь заблокирован или удалён")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require(*perms: Perm):
    """Зависимость, требующая наличия всех перечисленных прав у роли пользователя."""

    async def checker(user: CurrentUser, session: SessionDep) -> User:
        granted = await rbac.permissions_for(session, user.role)
        missing = [perm.value for perm in perms if perm not in granted]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав (роль {user.role}); требуется: {', '.join(missing)}",
            )
        return user

    return checker


async def get_server(server_id: int, session: SessionDep) -> OpensipsServer:
    server = await session.get(OpensipsServer, server_id)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сервер не найден")
    return server


ServerDep = Annotated[OpensipsServer, Depends(get_server)]


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


ClientIP = Annotated[str | None, Depends(client_ip)]
