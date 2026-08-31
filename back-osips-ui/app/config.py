"""Конфигурация приложения. Читается из переменных окружения или .env файла."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # --- общее ---
    APP_NAME: str = "osips-ui"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ROOT_PATH: str = ""

    # --- безопасность ---
    # SECRET_KEY используется для подписи JWT и для шифрования паролей от БД opensips.
    # ОБЯЗАТЕЛЬНО задать в проде: openssl rand -hex 32
    SECRET_KEY: str = "change-me-in-production-please-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 12 * 60
    # сколько секунд воркер держит матрицу прав в памяти (правки ролей доезжают за это время)
    RBAC_CACHE_TTL: int = 5
    JWT_ALGORITHM: str = "HS256"

    # --- БД приложения (SQLite) ---
    APP_DB_PATH: str = str(BASE_DIR / "data" / "osips-ui.db")

    # --- первый администратор (создаётся при первом запуске, если пользователей нет) ---
    BOOTSTRAP_ADMIN_USERNAME: str = "admin"
    BOOTSTRAP_ADMIN_PASSWORD: str = "admin"

    # --- раздача собранного фронтенда ---
    # В проде FastAPI сам отдаёт статику (nginx не нужен).
    STATIC_DIR: str = str(BASE_DIR.parent / "front-osips-ui" / "dist")
    SERVE_STATIC: bool = True

    # --- CORS (нужен только для локальной разработки, когда vite на другом порту) ---
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # --- работа с opensips ---
    MI_TIMEOUT: int = 5  # таймаут http MI запроса, сек
    OPENSIPS_DB_POOL_SIZE: int = 3
    OPENSIPS_DB_POOL_MAX_OVERFLOW: int = 2
    OPENSIPS_DB_CONNECT_TIMEOUT: int = 5

    # --- sip-регистрации ---
    SIPREGS_PAGE_SIZE: int = 25
    # ul_dump выгружает всю память usrloc и на большой базе отвечает долго - таймаут отдельный
    MI_DUMP_TIMEOUT: int = 15

    # --- dialplan и списки номеров ---
    DIALPLAN_PAGE_SIZE: int = 25
    BLACKLIST_PAGE_SIZE: int = 25

    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore")


settings = Settings()
