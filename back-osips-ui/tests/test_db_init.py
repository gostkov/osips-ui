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
