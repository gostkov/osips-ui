import os
import tempfile

os.environ.setdefault("APP_DB_PATH", os.path.join(tempfile.mkdtemp(), "test.db"))
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-0123456789abcdef")
os.environ.setdefault("SERVE_STATIC", "false")
os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "admin-test-pass")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def admin_headers(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin-test-pass"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="session")
def qa_headers(client, admin_headers):
    client.post("/api/users", headers=admin_headers, json={"username": "qa-user", "password": "qa-password", "role": "qa"})
    response = client.post("/api/auth/login", json={"username": "qa-user", "password": "qa-password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="session")
def reader_headers(client, admin_headers):
    client.post("/api/users", headers=admin_headers, json={"username": "reader-user", "password": "reader-password", "role": "reader"})
    response = client.post("/api/auth/login", json={"username": "reader-user", "password": "reader-password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="session")
def server_id(client, admin_headers):
    response = client.post(
        "/api/servers",
        headers=admin_headers,
        json={
            "name": "test-osips",
            "ip_address": "127.0.0.1",
            "mi_host": "127.0.0.1",
            "mi_port": 18888,
            "db_host": "127.0.0.1",
            "db_name": "opensips",
            "db_user": "opensips",
            "db_password": "secret",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]
