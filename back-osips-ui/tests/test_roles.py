"""Динамические роли: сидирование, CRUD, защита от самоблокировки."""

from app.core.roles import ADMIN_ROLE, PERM_GROUPS, Perm


def _by_slug(roles: list[dict]) -> dict[str, dict]:
    return {role["slug"]: role for role in roles}


def test_default_roles_are_seeded(client, admin_headers):
    roles = _by_slug(client.get("/api/roles", headers=admin_headers).json())
    assert set(roles) >= {ADMIN_ROLE, "qa", "hardwares", "reader"}

    admin = roles[ADMIN_ROLE]
    assert admin["is_builtin"] is True
    assert set(admin["permissions"]) == {perm.value for perm in Perm}
    # остальные роли обычные - их можно менять и удалять
    assert all(not roles[slug]["is_builtin"] for slug in ("qa", "hardwares", "reader"))


def test_permission_catalogue_covers_every_perm(client, admin_headers):
    groups = client.get("/api/roles/permissions", headers=admin_headers).json()
    listed = [item["value"] for group in groups for item in group["permissions"]]
    assert sorted(listed) == sorted(perm.value for perm in Perm)
    assert len(listed) == len(set(listed))
    assert len(groups) == len(PERM_GROUPS)


def test_role_is_not_available_without_users_manage(client, qa_headers):
    assert client.get("/api/roles", headers=qa_headers).status_code == 403
    assert client.post("/api/roles", headers=qa_headers, json={"slug": "x", "title": "X"}).status_code == 403


def test_create_role_and_apply_it_to_user(client, admin_headers):
    created = client.post(
        "/api/roles",
        headers=admin_headers,
        json={
            "slug": "noc",
            "title": "Дежурная смена",
            "description": "Выводит ноды из обслуживания",
            "permissions": ["servers:read", "dispatcher:read", "dispatcher:write"],
        },
    )
    assert created.status_code == 201, created.text
    role_id = created.json()["id"]
    assert created.json()["users_count"] == 0

    client.post("/api/users", headers=admin_headers, json={"username": "noc-user", "password": "noc-password", "role": "noc"})
    headers = {"Authorization": f"Bearer {client.post('/api/auth/login', json={'username': 'noc-user', 'password': 'noc-password'}).json()['access_token']}"}

    me = client.get("/api/auth/me", headers=headers).json()
    assert me["role"] == "noc"
    assert set(me["permissions"]) == {"servers:read", "dispatcher:read", "dispatcher:write"}

    # правка прав видна сразу - кеш матрицы сбрасывается при записи
    client.put(f"/api/roles/{role_id}", headers=admin_headers, json={"permissions": ["servers:read", "sipregs:read"]})
    assert set(client.get("/api/auth/me", headers=headers).json()["permissions"]) == {"servers:read", "sipregs:read"}
    assert client.get("/api/servers/1/dispatcher", headers=headers).status_code == 403

    # роль занята пользователем - удалять нельзя
    conflict = client.delete(f"/api/roles/{role_id}", headers=admin_headers)
    assert conflict.status_code == 409

    users = {user["username"]: user for user in client.get("/api/users", headers=admin_headers).json()}
    client.put(f"/api/users/{users['noc-user']['id']}", headers=admin_headers, json={"role": "reader"})
    assert client.delete(f"/api/roles/{role_id}", headers=admin_headers).status_code == 200


def test_renaming_role_moves_its_users(client, admin_headers):
    role_id = client.post(
        "/api/roles", headers=admin_headers, json={"slug": "old-name", "title": "Старое имя", "permissions": ["sipregs:read"]}
    ).json()["id"]
    client.post("/api/users", headers=admin_headers, json={"username": "renamed-user", "password": "renamed-password", "role": "old-name"})

    assert client.put(f"/api/roles/{role_id}", headers=admin_headers, json={"slug": "new-name"}).status_code == 200

    users = {user["username"]: user for user in client.get("/api/users", headers=admin_headers).json()}
    assert users["renamed-user"]["role"] == "new-name"


def test_builtin_admin_role_is_protected(client, admin_headers):
    roles = _by_slug(client.get("/api/roles", headers=admin_headers).json())
    admin_id = roles[ADMIN_ROLE]["id"]
    assert client.put(f"/api/roles/{admin_id}", headers=admin_headers, json={"permissions": []}).status_code == 403
    assert client.delete(f"/api/roles/{admin_id}", headers=admin_headers).status_code == 403


def test_cannot_drop_users_manage_from_own_role(client, admin_headers):
    # своя роль администратора встроенная, поэтому проверяем на отдельной роли с users:manage
    role_id = client.post(
        "/api/roles",
        headers=admin_headers,
        json={"slug": "co-admin", "title": "Со-администратор", "permissions": ["users:manage", "servers:read"]},
    ).json()["id"]
    client.post("/api/users", headers=admin_headers, json={"username": "co-admin", "password": "co-admin-password", "role": "co-admin"})
    headers = {"Authorization": f"Bearer {client.post('/api/auth/login', json={'username': 'co-admin', 'password': 'co-admin-password'}).json()['access_token']}"}

    denied = client.put(f"/api/roles/{role_id}", headers=headers, json={"permissions": ["servers:read"]})
    assert denied.status_code == 400
    assert "своей собственной роли" in denied.json()["detail"]

    # чужую роль тот же пользователь менять может
    other = _by_slug(client.get("/api/roles", headers=headers).json())["reader"]
    assert client.put(f"/api/roles/{other['id']}", headers=headers, json={"permissions": ["sipregs:read"]}).status_code == 200


def test_cannot_assign_self_role_without_users_manage(client, admin_headers):
    me = client.get("/api/auth/me", headers=admin_headers).json()
    denied = client.put(f"/api/users/{me['id']}", headers=admin_headers, json={"role": "reader"})
    assert denied.status_code == 400

    unknown = client.put(f"/api/users/{me['id']}", headers=admin_headers, json={"role": "no-such-role"})
    assert unknown.status_code == 400
