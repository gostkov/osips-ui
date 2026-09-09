# Прод-образ: собранный фронтенд и backend в одном контейнере, gunicorn на 8000.
# Контекст сборки - корень репозитория:
#   docker build -f install/Dockerfile -t osips-ui:1.0.0 .
# либо через install/docker-compose.prod.yml.

# --- 1. фронтенд ------------------------------------------------------------
FROM node:22-alpine AS frontend

WORKDIR /build
COPY front-osips-ui/package.json front-osips-ui/package-lock.json ./
RUN npm ci
COPY front-osips-ui/ ./
RUN npm run build

# --- 2. зависимости backend -------------------------------------------------
FROM python:3.11-slim-bookworm AS backend

ENV PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.3.2 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true

WORKDIR /opt/osips-ui/back-osips-ui

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"
COPY back-osips-ui/pyproject.toml back-osips-ui/poetry.lock ./
RUN poetry check --lock && poetry install --only main --no-root

# --- 3. рантайм -------------------------------------------------------------
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/osips-ui/back-osips-ui/.venv/bin:$PATH" \
    APP_DB_PATH=/data/osips-ui.db \
    STATIC_DIR=/opt/osips-ui/front-osips-ui/dist \
    SERVE_STATIC=true \
    CORS_ORIGINS=[] \
    DEBUG=false

WORKDIR /opt/osips-ui/back-osips-ui

RUN useradd --system --uid 10001 --home-dir /opt/osips-ui --shell /usr/sbin/nologin osips-ui \
    && mkdir -p /data \
    && chown osips-ui:osips-ui /data

COPY --from=backend /opt/osips-ui/back-osips-ui/.venv ./.venv
COPY back-osips-ui/app ./app
COPY back-osips-ui/gunicorn_conf.py ./
COPY --from=frontend /build/dist /opt/osips-ui/front-osips-ui/dist

USER osips-ui
# база приложения (пользователи, роли, реестр серверов, журнал) переживает пересоздание контейнера
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3).status == 200 else 1)"

CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]
