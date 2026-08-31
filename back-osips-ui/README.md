# back-osips-ui

Backend web-интерфейса управления OpenSIPS (FastAPI).

Документация по сборке, запуску и конфигурации — в [README.md](../README.md) корня репозитория.

Быстрый старт для разработки:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000   # Swagger: http://127.0.0.1:8000/docs
PYTHONPATH=. pytest -q                      # тесты
```
