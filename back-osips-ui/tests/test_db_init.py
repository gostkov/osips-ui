"""Первичная инициализация БД при нескольких воркерах gunicorn.

Воркеры стартуют одновременно и на пустой базе наперегонки выполняют create_all
и первичное наполнение. Без межпроцессной блокировки проигравший получал
"database is locked" и падал, а gunicorn гасил на этом всю службу.
"""

import os
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BACK_DIR = Path(__file__).resolve().parent.parent

# то же, что делает lifespan приложения на старте воркера
WORKER = "import asyncio; from app.db.session import init_db; asyncio.run(init_db())"


def _spawn_worker(db_path: Path) -> subprocess.CompletedProcess:
    env = os.environ | {"APP_DB_PATH": str(db_path), "PYTHONPATH": str(BACK_DIR), "DEBUG": "false"}
    return subprocess.run([sys.executable, "-c", WORKER], cwd=BACK_DIR, env=env, capture_output=True, text=True)


def test_parallel_init_db(tmp_path):
    db_path = tmp_path / "osips-ui.db"
    workers = 4

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda _: _spawn_worker(db_path), range(workers)))

    for result in results:
        assert result.returncode == 0, f"воркер упал:\n{result.stderr}"

    from app.core.roles import DEFAULT_ROLES

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM roles").fetchone()[0] == len(DEFAULT_ROLES)


def test_existing_users_receive_stable_auth_ids(tmp_path):
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("""CREATE TABLE users (
            id INTEGER PRIMARY KEY, username VARCHAR(64) NOT NULL UNIQUE,
            full_name VARCHAR(128), email VARCHAR(128), password_hash VARCHAR(128),
            role VARCHAR(32) NOT NULL, is_active BOOLEAN NOT NULL,
            auth_provider VARCHAR(32) NOT NULL, external_id VARCHAR(128),
            created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL, last_login_at DATETIME
        )""")
        conn.executemany(
            "INSERT INTO users (username, password_hash, role, is_active, auth_provider, created_at, updated_at) "
            "VALUES (?, 'unchanged-hash', 'admin', 1, 'local', '2026-01-01', '2026-01-01')",
            [("existing-admin",), ("second-user",)],
        )
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda _: _spawn_worker(db_path), range(3)))
    for result in results:
        assert result.returncode == 0, result.stderr
    with sqlite3.connect(db_path) as conn:
        before = conn.execute("SELECT username, password_hash, auth_id FROM users ORDER BY id").fetchall()
    assert len(before) == 2
    assert len({row[2] for row in before}) == 2
    assert all(len(row[2]) == 32 and row[1] == "unchanged-hash" for row in before)
    assert _spawn_worker(db_path).returncode == 0
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT username, password_hash, auth_id FROM users ORDER BY id").fetchall() == before
