"""Управление пользователями. Доступно тем, у кого есть users:manage."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from ..core.deps import ClientIP, CurrentUser, SessionDep, require
from ..core.roles import Perm
from ..core.security import hash_password
from ..db.audit import write_audit
from ..db.models import Role, User
from ..schemas.user import UserCreate, UserOut, UserUpdate
from ..services import rbac

router = APIRouter(prefix="/api/users", tags=["users"], dependencies=[Depends(require(Perm.USERS_MANAGE))])


@router.get("", response_model=list[UserOut], summary="Список пользователей")
async def list_users(session: SessionDep) -> list[User]:
    result = await session.scalars(select(User).order_by(User.username))
    return list(result)


async def _check_role_exists(session: SessionDep, slug: str) -> None:
    if not await session.scalar(select(Role.id).where(Role.slug == slug)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Роль '{slug}' не найдена")


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Создать пользователя")
async def create_user(payload: UserCreate, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> User:
    exists = await session.scalar(select(User.id).where(User.username == payload.username))
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь с таким логином уже есть")
    await _check_role_exists(session, payload.role)

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        role=payload.role,
        is_active=payload.is_active,
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    await session.commit()
    await write_audit(session, user=actor, action="users.create", target=user.username, details={"role": user.role}, client_ip=ip)
    return user


@router.put("/{user_id}", response_model=UserOut, summary="Изменить пользователя (в т.ч. роль)")
async def update_user(user_id: int, payload: UserUpdate, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    data = payload.model_dump(exclude_unset=True)
    new_role = data.get("role")
    if new_role:
        await _check_role_exists(session, new_role)

    if user.id == actor.id:
        # иначе администратор может лишить себя доступа к разделу и никого больше не назначит
        if new_role and new_role != user.role and not await rbac.has_perm(session, new_role, Perm.USERS_MANAGE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Нельзя перевести себя на роль '{new_role}': у неё нет права «Пользователи и роли»",
            )
        if data.get("is_active") is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя заблокировать самого себя")

    if "password" in data:
        password = data.pop("password")
        if password:
            user.password_hash = hash_password(password)
    for field, value in data.items():
        setattr(user, field, value)
    await session.commit()
    await write_audit(session, user=actor, action="users.update", target=user.username, details=data, client_ip=ip)
    return user


@router.delete("/{user_id}", summary="Удалить пользователя")
async def delete_user(user_id: int, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    if user.id == actor.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить самого себя")

    username = user.username
    await session.delete(user)
    await session.commit()
    await write_audit(session, user=actor, action="users.delete", target=username, client_ip=ip)
    return {"ok": True}
