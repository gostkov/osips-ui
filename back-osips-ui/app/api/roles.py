"""Роли и их права. Доступно тем, у кого есть users:manage."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update

from ..core.deps import ClientIP, CurrentUser, SessionDep, require
from ..core.roles import PERM_GROUPS, Perm
from ..db.audit import write_audit
from ..db.models import Role, RolePermission, User
from ..schemas.role import PermissionGroupOut, RoleCreate, RoleOut, RoleUpdate
from ..services import rbac

router = APIRouter(prefix="/api/roles", tags=["roles"], dependencies=[Depends(require(Perm.USERS_MANAGE))])


def _to_out(role: Role, users_count: int) -> RoleOut:
    return RoleOut(
        id=role.id,
        slug=role.slug,
        title=role.title,
        description=role.description,
        is_builtin=role.is_builtin,
        permissions=sorted(item.permission for item in role.permissions),
        users_count=users_count,
        created_at=role.created_at,
    )


async def _users_by_role(session: SessionDep) -> dict[str, int]:
    rows = await session.execute(select(User.role, func.count(User.id)).group_by(User.role))
    return {slug: count for slug, count in rows}


async def _get_role(session: SessionDep, role_id: int) -> Role:
    role = await session.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль не найдена")
    return role


@router.get("", response_model=list[RoleOut], summary="Список ролей")
async def list_roles(session: SessionDep) -> list[RoleOut]:
    roles = (await session.scalars(select(Role).order_by(Role.is_builtin.desc(), Role.slug))).all()
    counts = await _users_by_role(session)
    return [_to_out(role, counts.get(role.slug, 0)) for role in roles]


@router.get("/permissions", response_model=list[PermissionGroupOut], summary="Каталог прав по разделам")
async def list_permissions() -> list[dict]:
    return PERM_GROUPS


@router.post("", response_model=RoleOut, status_code=status.HTTP_201_CREATED, summary="Создать роль")
async def create_role(payload: RoleCreate, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> RoleOut:
    if await session.scalar(select(Role.id).where(Role.slug == payload.slug)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Роль с таким кодом уже есть")

    role = Role(
        slug=payload.slug,
        title=payload.title,
        description=payload.description,
        permissions=[RolePermission(permission=perm.value) for perm in dict.fromkeys(payload.permissions)],
    )
    session.add(role)
    await session.commit()
    rbac.invalidate()
    await write_audit(
        session,
        user=actor,
        action="roles.create",
        target=role.slug,
        details={"permissions": [perm.value for perm in payload.permissions]},
        client_ip=ip,
    )
    return _to_out(role, 0)


@router.put("/{role_id}", response_model=RoleOut, summary="Изменить роль")
async def update_role(role_id: int, payload: RoleUpdate, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> RoleOut:
    role = await _get_role(session, role_id)
    if role.is_builtin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Встроенная роль '{role.slug}' не редактируется: она гарантирует полный доступ хотя бы одному пользователю",
        )

    data = payload.model_dump(exclude_unset=True)
    permissions = data.pop("permissions", None)

    # защита от самоблокировки: снять users:manage с собственной роли нельзя
    if permissions is not None and role.slug == actor.role and Perm.USERS_MANAGE not in permissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя убрать право «Пользователи и роли» у своей собственной роли",
        )

    new_slug = data.pop("slug", None)
    if new_slug and new_slug != role.slug:
        if await session.scalar(select(Role.id).where(Role.slug == new_slug)):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Роль с таким кодом уже есть")
        await session.execute(update(User).where(User.role == role.slug).values(role=new_slug))
        role.slug = new_slug

    for field, value in data.items():
        setattr(role, field, value)

    if permissions is not None:
        # существующие строки переиспользуем: если пересоздавать список целиком, вставка
        # новых строк уезжает раньше удаления старых и ловит UNIQUE(role_id, permission)
        wanted = {perm.value for perm in permissions}
        current = {item.permission for item in role.permissions}
        role.permissions = [item for item in role.permissions if item.permission in wanted] + [
            RolePermission(permission=value) for value in sorted(wanted - current)
        ]

    await session.commit()
    rbac.invalidate()
    await write_audit(
        session,
        user=actor,
        action="roles.update",
        target=role.slug,
        details={"permissions": sorted(item.permission for item in role.permissions)} | data,
        client_ip=ip,
    )
    counts = await _users_by_role(session)
    return _to_out(role, counts.get(role.slug, 0))


@router.delete("/{role_id}", summary="Удалить роль")
async def delete_role(role_id: int, session: SessionDep, actor: CurrentUser, ip: ClientIP) -> dict:
    role = await _get_role(session, role_id)
    if role.is_builtin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Встроенную роль '{role.slug}' удалить нельзя")

    counts = await _users_by_role(session)
    in_use = counts.get(role.slug, 0)
    if in_use:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Роль назначена пользователям ({in_use}). Сначала переведите их на другую роль.",
        )

    slug = role.slug
    await session.delete(role)
    await session.commit()
    rbac.invalidate()
    await write_audit(session, user=actor, action="roles.delete", target=slug, client_ip=ip)
    return {"ok": True}
