# back-osips-ui

Backend web-интерфейса управления OpenSIPS (FastAPI).

Документация по сборке, запуску и конфигурации — в [README.md](../README.md) корня репозитория.

Быстрый старт для разработки:

```bash
poetry install                              # venv и зависимости строго по poetry.lock
cp .env.example .env
poetry run uvicorn app.main:app --reload --port 8000   # Swagger: http://127.0.0.1:8000/docs
poetry run pytest -q                        # тесты
```
