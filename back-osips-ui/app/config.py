"""Конфигурация приложения. Читается из переменных окружения или .env файла."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

# значения из репозитория: с ними приложение в проде стартовать откажется
DEFAULT_SECRET_KEY = "change-me-in-production-please-use-openssl-rand-hex-32"
DEFAULT_ADMIN_PASSWORD = "admin"
MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    # --- общее ---
    APP_NAME: str = "osips-ui"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ROOT_PATH: str = ""

    # --- безопасность ---
    # SECRET_KEY используется для подписи JWT и для шифрования паролей от БД opensips.
    # ОБЯЗАТЕЛЬНО задать в проде: openssl rand -hex 32
    SECRET_KEY: str = DEFAULT_SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 12 * 60
    # сколько секунд воркер держит матрицу прав в памяти (правки ролей доезжают за это время)
    RBAC_CACHE_TTL: int = 5
    JWT_ALGORITHM: str = "HS256"

    # --- БД приложения (SQLite) ---
    APP_DB_PATH: str = str(BASE_DIR / "data" / "osips-ui.db")
    # сколько секунд ждать снятия блокировки SQLite, прежде чем отдать "database is locked"
    APP_DB_TIMEOUT: int = 30

    # --- первый администратор (создаётся при первом запуске, если пользователей нет) ---
    BOOTSTRAP_ADMIN_USERNAME: str = "admin"
    BOOTSTRAP_ADMIN_PASSWORD: str = DEFAULT_ADMIN_PASSWORD

    # --- документация API ---
    # /docs, /redoc и /openapi.json отдаются без авторизации: на закрытом контуре это удобно,
    # на публичном - лишняя карта API, тогда выключайте
    DOCS_ENABLED: bool = True

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


def verify_production_secrets() -> None:
    """В проде (DEBUG=false) отказываемся стартовать с ключом из .env.example.

    SECRET_KEY подписывает JWT: с известным значением любой желающий выпишет себе
    токен с ролью admin. Лучше не подняться, чем подняться беззащитным.
    """
    if settings.DEBUG:
        return
    if settings.SECRET_KEY == DEFAULT_SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY остался значением по умолчанию из .env.example. "
            "Задайте свой: SECRET_KEY=$(openssl rand -hex 32) - либо включите DEBUG=true для локальной разработки."
        )
    if len(settings.SECRET_KEY) < MIN_SECRET_KEY_LENGTH:
        raise RuntimeError(
            f"SECRET_KEY короче {MIN_SECRET_KEY_LENGTH} символов. Сгенерируйте нормальный: openssl rand -hex 32"
        )
