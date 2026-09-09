# Сборка в два этапа: poetry ставит зависимости по poetry.lock в отдельный venv,
# в финальный образ едет только этот venv - без poetry и без кеша сборки.
FROM python:3.11-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.3.2 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true

WORKDIR /opt/osips-ui/back-osips-ui

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

# сначала только манифесты: слой с зависимостями переиспользуется, пока не менялся poetry.lock
COPY pyproject.toml poetry.lock ./
RUN poetry check --lock && poetry install --only main --no-root

FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/osips-ui/back-osips-ui/.venv/bin:$PATH"

WORKDIR /opt/osips-ui/back-osips-ui

COPY --from=builder /opt/osips-ui/back-osips-ui/.venv ./.venv
COPY app ./app
COPY gunicorn_conf.py ./

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
