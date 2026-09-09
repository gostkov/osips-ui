"""Защитные механизмы: заголовки ответов, отказ стартовать с секретами из репозитория,
сокращённая карточка сервера для тех, у кого нет servers:read.
"""

import pytest

from app import config
from app.config import DEFAULT_SECRET_KEY, verify_production_secrets


def test_security_headers_present(client):
    response = client.get("/api/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    csp = response.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "object-src 'none'" in csp


def test_hsts_only_behind_https(client):
    assert "Strict-Transport-Security" not in client.get("/api/health").headers
    forwarded = client.get("/api/health", headers={"X-Forwarded-Proto": "https"})
    assert forwarded.headers["Strict-Transport-Security"].startswith("max-age=")


def test_swagger_without_csp(client):
    """Swagger UI тянет скрипты с cdn.jsdelivr.net, под нашей CSP он бы не открылся."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Content-Security-Policy" not in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_default_secret_key_refused_in_production(monkeypatch):
    monkeypatch.setattr(config.settings, "DEBUG", False)
    monkeypatch.setattr(config.settings, "SECRET_KEY", DEFAULT_SECRET_KEY)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        verify_production_secrets()


def test_short_secret_key_refused_in_production(monkeypatch):
    monkeypatch.setattr(config.settings, "DEBUG", False)
    monkeypatch.setattr(config.settings, "SECRET_KEY", "too-short")
    with pytest.raises(RuntimeError, match="короче"):
        verify_production_secrets()


def test_default_secret_key_allowed_in_debug(monkeypatch):
    """Локальной разработке ключ не нужен - иначе поднять стенд станет мучением."""
    monkeypatch.setattr(config.settings, "DEBUG", True)
    monkeypatch.setattr(config.settings, "SECRET_KEY", DEFAULT_SECRET_KEY)
    verify_production_secrets()


def test_own_secret_key_passes(monkeypatch):
    monkeypatch.setattr(config.settings, "DEBUG", False)
    monkeypatch.setattr(config.settings, "SECRET_KEY", "a" * 64)
    verify_production_secrets()


@pytest.fixture(scope="module")
def dialplan_only_headers(client, admin_headers):
    """Роль с единственным правом dialplan:read - без servers:read."""
    client.post(
        "/api/roles",
        headers=admin_headers,
        json={"slug": "dialplan-only", "title": "Только dialplan", "permissions": ["dialplan:read"]},
    )
    client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "dialplan-only-user", "password": "dialplan-password", "role": "dialplan-only"},
    )
    response = client.post("/api/auth/login", json={"username": "dialplan-only-user", "password": "dialplan-password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_server_registry_hidden_without_servers_read(client, dialplan_only_headers, server_id):
    """Селектор серверов нужен всем, реквизиты инфраструктуры - только по servers:read."""
    response = client.get("/api/servers", headers=dialplan_only_headers)
    assert response.status_code == 200
    item = next(row for row in response.json() if row["id"] == server_id)
    assert item["name"]  # имя для селектора видно
    for hidden in ("ip_address", "db_host", "db_name", "db_user", "mi_host", "mi_username"):
        assert item[hidden] is None, hidden

    assert client.get(f"/api/servers/{server_id}", headers=dialplan_only_headers).status_code == 403
    assert client.post(f"/api/servers/{server_id}/check", headers=dialplan_only_headers).status_code == 403


@pytest.fixture(scope="module")
def servers_read_headers(client, admin_headers):
    """Своя роль с servers:read: у встроенной reader права правит test_roles.py."""
    client.post(
        "/api/roles",
        headers=admin_headers,
        json={"slug": "servers-viewer", "title": "Смотрит реестр", "permissions": ["servers:read"]},
    )
    client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "servers-viewer-user", "password": "viewer-password", "role": "servers-viewer"},
    )
    response = client.post("/api/auth/login", json={"username": "servers-viewer-user", "password": "viewer-password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_server_registry_full_with_servers_read(client, servers_read_headers, server_id):
    item = next(row for row in client.get("/api/servers", headers=servers_read_headers).json() if row["id"] == server_id)
    assert item["ip_address"] is not None
    assert item["db_host"] is not None
    assert client.post(f"/api/servers/{server_id}/check", headers=servers_read_headers).status_code == 200

