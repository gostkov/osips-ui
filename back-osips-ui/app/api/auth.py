"""Аутентификация: логин по паролю, профиль, смена пароля.

Задел под SSO: точка входа /api/auth/login оставляет место для второго провайдера -
пользователь с auth_provider != 'local' по паролю войти не может.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from ..config import settings
from ..core.deps import ClientIP, CurrentUser, SessionDep
from ..services import rbac
from ..core.security import create_access_token, hash_password, verify_password
from ..db.audit import write_audit
from ..db.models import User
from ..schemas.user import ChangePasswordRequest, LoginRequest, MeOut, TokenOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


async def _me(session: SessionDep, user: User) -> MeOut:
    granted = await rbac.permissions_for(session, user.role)
    return MeOut.model_validate(user, from_attributes=True).model_copy(
        update={"permissions": sorted(perm.value for perm in granted)}
    )


async def _authenticate(session: SessionDep, username: str, password: str) -> User:
    user = await session.scalar(select(User).where(User.username == username))
    if user is None or not user.is_active or user.auth_provider != "local" or not user.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
    return user


async def _issue_token(session: SessionDep, user: User, client_ip: str | None) -> TokenOut:
    user.last_login_at = datetime.now(UTC).replace(tzinfo=None)
    await session.commit()
    await write_audit(session, user=user, action="auth.login", client_ip=client_ip)
    return TokenOut(
        access_token=create_access_token(user.username, user.role),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=await _me(session, user),
    )


@router.post("/login", response_model=TokenOut, summary="Вход по логину и паролю")
async def login(payload: LoginRequest, session: SessionDep, ip: ClientIP) -> TokenOut:
    user = await _authenticate(session, payload.username, payload.password)
    return await _issue_token(session, user, ip)


@router.post("/token", response_model=TokenOut, summary="Вход через OAuth2 password flow (для Swagger)")
async def login_form(session: SessionDep, ip: ClientIP, form: OAuth2PasswordRequestForm = Depends()) -> TokenOut:
    user = await _authenticate(session, form.username, form.password)
    return await _issue_token(session, user, ip)


@router.get("/me", response_model=MeOut, summary="Текущий пользователь и его права")
async def me(user: CurrentUser, session: SessionDep) -> MeOut:
    return await _me(session, user)


@router.post("/change-password", summary="Смена собственного пароля")
async def change_password(payload: ChangePasswordRequest, user: CurrentUser, session: SessionDep, ip: ClientIP) -> dict:
    if user.auth_provider != "local" or not user.password_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пароль задаётся во внешней системе аутентификации")
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Текущий пароль указан неверно")
    user.password_hash = hash_password(payload.new_password)
    await session.commit()
    await write_audit(session, user=user, action="auth.change_password", client_ip=ip)
    return {"ok": True}
