"""Конфигурация gunicorn для прод-запуска (systemd)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class GunicornSettings(BaseSettings):
    GUNICORN_LISTEN: str = "0.0.0.0:8000"
    GUNICORN_WORKERS: int = 2
    GUNICORN_LOGLEVEL: str = "info"
    GUNICORN_TIMEOUT: int = 60

    model_config = SettingsConfigDict(env_file=str(Path(__file__).resolve().parent / ".env"), extra="ignore")


settings = GunicornSettings()

bind = settings.GUNICORN_LISTEN
workers = settings.GUNICORN_WORKERS
worker_class = "uvicorn.workers.UvicornWorker"
loglevel = settings.GUNICORN_LOGLEVEL
timeout = settings.GUNICORN_TIMEOUT
accesslog = "-"
errorlog = "-"
