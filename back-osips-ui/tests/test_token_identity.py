"""JWT должен принадлежать конкретной учётной записи, а не переиспользуемому логину."""

import jwt

from app.config import settings
from app.core.security import decode_access_token


def test_deleted_account_token_cannot_access_recreated_account(client, admin_headers):
    payload = {"username": "recreated-account", "password": "first-password", "role": "reader"}
    created = client.post("/api/users", headers=admin_headers, json=payload)
    assert created.status_code == 201
    login = client.post("/api/auth/login", json={"username": payload["username"], "password": payload["password"]})
    token = login.json()["access_token"]
    old_headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/auth/me", headers=old_headers).status_code == 200

    assert client.delete(f"/api/users/{created.json()['id']}", headers=admin_headers).status_code == 200
    assert client.get("/api/auth/me", headers=old_headers).status_code in (401, 403)
    replacement = client.post("/api/users", headers=admin_headers, json=payload | {"password": "second-password", "role": "admin"})
    assert replacement.status_code == 201
    try:
        assert client.get("/api/auth/me", headers=old_headers).status_code in (401, 403)
        assert client.get("/api/users", headers=old_headers).status_code in (401, 403)
        fresh = client.post("/api/auth/login", json={"username": payload["username"], "password": "second-password"})
        assert fresh.status_code == 200
        new_token = fresh.json()["access_token"]
        assert decode_access_token(new_token)["sub"] != decode_access_token(token)["sub"]
        assert client.get("/api/users", headers={"Authorization": f"Bearer {new_token}"}).status_code == 200
    finally:
        client.delete(f"/api/users/{replacement.json()['id']}", headers=admin_headers)


def test_legacy_username_token_requires_new_login(client, admin_headers):
    payload = decode_access_token(admin_headers["Authorization"].split()[1])
    payload.pop("ver")
    payload["sub"] = "admin"
    legacy = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {legacy}"}).status_code == 401
    assert client.get("/api/auth/me", headers=admin_headers).status_code == 200
