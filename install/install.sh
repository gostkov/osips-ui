#!/usr/bin/env bash
#
# Установка osips-ui на хост под systemd.
# Одна служба отдаёт и API, и собранный фронтенд на одном порту - nginx не нужен.
#
#   sudo install/install.sh                          полная установка из клона репозитория
#
# Ключи:
#   -d, --install-dir DIR   каталог установки (по умолчанию /opt/osips-ui)
#   -u, --user USER         системный пользователь службы (osips-ui)
#   -n, --service-name NAME имя службы systemd (osips-ui)
#   -l, --listen ADDR:PORT  адрес и порт gunicorn (0.0.0.0:8000)
#   -w, --workers N         число воркеров gunicorn (2)
#       --skip-frontend     dist уже собран (например, на build-хосте), node не нужен
#       --no-service        только разложить файлы, systemd не трогать
#   -h, --help              эта справка
#
# То же можно задать переменными окружения: INSTALL_DIR, SERVICE_USER, SERVICE_NAME,
# LISTEN, WORKERS, POETRY_HOME, POETRY_VERSION (ключ важнее переменной).
#
# Повторный запуск = обновление: код и зависимости обновятся, .env и база останутся.
# Если указать другой --install-dir, установка переедет: служба остановится, .env и база
# переберутся на новое место, старый каталог останется на диске нетронутым.

set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/osips-ui}"
SERVICE_USER="${SERVICE_USER:-osips-ui}"
SERVICE_NAME="${SERVICE_NAME:-osips-ui}"
LISTEN="${LISTEN:-0.0.0.0:8000}"
WORKERS="${WORKERS:-2}"
POETRY_HOME="${POETRY_HOME:-/opt/poetry}"
POETRY_VERSION="${POETRY_VERSION:-2.3.2}"

SKIP_FRONTEND=0
WITH_SERVICE=1
# ключи, заданные явно, перебивают уже существующий .env
LISTEN_SET=0
WORKERS_SET=0

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GENERATED_PASSWORD=""

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
    sed -n '2,25p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 0
}

need_value() { [ -n "${2:-}" ] || die "Ключу $1 нужно значение"; }

while [ $# -gt 0 ]; do
    case "$1" in
        -d|--install-dir)  need_value "$1" "${2:-}"; INSTALL_DIR="$2"; shift ;;
        -u|--user)         need_value "$1" "${2:-}"; SERVICE_USER="$2"; shift ;;
        -n|--service-name) need_value "$1" "${2:-}"; SERVICE_NAME="$2"; shift ;;
        -l|--listen)       need_value "$1" "${2:-}"; LISTEN="$2"; LISTEN_SET=1; shift ;;
        -w|--workers)      need_value "$1" "${2:-}"; WORKERS="$2"; WORKERS_SET=1; shift ;;
        --skip-frontend)   SKIP_FRONTEND=1 ;;
        --no-service)      WITH_SERVICE=0 ;;
        -h|--help)         usage ;;
        *)                 die "Неизвестный аргумент: $1 (--help для справки)" ;;
    esac
    shift
done

# каталог установки станет собственностью служебного пользователя и будет
# перезаписан кодом, поэтому системные каталоги под него отдавать нельзя
case "$INSTALL_DIR" in
    /*) ;;
    *)  die "--install-dir должен быть абсолютным путём, получено: $INSTALL_DIR" ;;
esac
INSTALL_DIR="${INSTALL_DIR%/}"
case "$INSTALL_DIR" in
    ""|/|/usr|/etc|/var|/opt|/srv|/home|/root|/boot|/tmp|/bin|/sbin|/lib|/dev|/proc|/sys)
        die "Небезопасный каталог установки: ${INSTALL_DIR:-/}. Укажите отдельный подкаталог, например /opt/osips-ui" ;;
esac

BACK_DIR="$INSTALL_DIR/back-osips-ui"
FRONT_DIR="$INSTALL_DIR/front-osips-ui"
ENV_FILE="$BACK_DIR/.env"
UNIT_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# --- 1. проверки окружения ------------------------------------------------

[ "$(id -u)" -eq 0 ] || die "Запускать от root: sudo install/install.sh"

command -v python3 >/dev/null || die "Не найден python3 (нужен 3.11+)"
python3 - <<'PY' || die "Нужен python 3.11 или новее"
import sys
sys.exit(0 if sys.version_info >= (3, 11) else 1)
PY

command -v openssl >/dev/null || die "Не найден openssl (нужен для генерации SECRET_KEY)"

if [ "$SKIP_FRONTEND" -eq 0 ]; then
    command -v npm >/dev/null || die "Не найден npm (нужен node 22+), либо соберите dist заранее и запустите с --skip-frontend"
    node_major="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
    [ "$node_major" -ge 22 ] || warn "node $(node --version 2>/dev/null): проект собирался на 22+, сборка может не пройти"
elif [ ! -f "$REPO_DIR/front-osips-ui/dist/index.html" ]; then
    die "--skip-frontend, но $REPO_DIR/front-osips-ui/dist/index.html не найден"
fi

if [ "$WITH_SERVICE" -eq 1 ]; then
    command -v systemctl >/dev/null || die "Нет systemctl. Для установки без systemd используйте --no-service"
fi

# --- 2. системный пользователь --------------------------------------------

if id -u "$SERVICE_USER" >/dev/null 2>&1; then
    log "Пользователь $SERVICE_USER уже есть"
else
    log "Создаю системного пользователя $SERVICE_USER"
    useradd --system --home-dir "$INSTALL_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
fi

# --- 3. переезд с прежнего пути --------------------------------------------

# Каталог установки прописан в unit-файле, из него и узнаём, где стояла прошлая версия.
previous_install_dir() {
    [ -f "$UNIT_FILE" ] || return 1
    sed -n 's|^WorkingDirectory=\(.*\)/back-osips-ui[[:space:]]*$|\1|p' "$UNIT_FILE" | head -1
}

PREV_DIR="$(previous_install_dir || true)"
MIGRATED_ENV=0

if [ -n "$PREV_DIR" ] && [ "$PREV_DIR" != "$INSTALL_DIR" ] && [ -d "$PREV_DIR" ]; then
    log "Прежняя установка в $PREV_DIR, переезжаю в $INSTALL_DIR"
    if [ "$WITH_SERVICE" -eq 1 ] && command -v systemctl >/dev/null; then
        systemctl stop "$SERVICE_NAME" >/dev/null 2>&1 || true
    fi
    mkdir -p "$BACK_DIR/data"
    if [ -f "$PREV_DIR/back-osips-ui/.env" ] && [ ! -f "$ENV_FILE" ]; then
        cp -a "$PREV_DIR/back-osips-ui/.env" "$ENV_FILE"
        MIGRATED_ENV=1
        log "Настройки перенесены из $PREV_DIR/back-osips-ui/.env"
    fi
    if [ -d "$PREV_DIR/back-osips-ui/data" ] && [ -z "$(ls -A "$BACK_DIR/data" 2>/dev/null)" ]; then
        cp -a "$PREV_DIR/back-osips-ui/data/." "$BACK_DIR/data/"
        log "База приложения перенесена из $PREV_DIR/back-osips-ui/data"
    fi
fi

# --- 4. код в каталог установки -------------------------------------------

if [ "$REPO_DIR" = "$INSTALL_DIR" ]; then
    log "Запуск из каталога установки, копирование не нужно"
else
    log "Копирую код в $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    # .env, data/ и .venv целевого каталога не трогаем - это состояние, а не код
    tar -C "$REPO_DIR" \
        --exclude=./.git \
        --exclude=./front-osips-ui/node_modules \
        --exclude=./back-osips-ui/.venv \
        --exclude=./back-osips-ui/data \
        --exclude=./back-osips-ui/.env \
        --exclude=./back-osips-ui/.pytest_cache \
        --exclude='./**/__pycache__' \
        --exclude=./dev \
        --exclude=./docker-compose.yml \
        -cf - . | tar -C "$INSTALL_DIR" -xf -
fi

# --- 5. poetry --------------------------------------------------------------

find_poetry() {
    local candidate
    for candidate in "$POETRY_HOME/bin/poetry" "$(command -v poetry || true)"; do
        [ -n "$candidate" ] && [ -x "$candidate" ] || continue
        # poetry.lock версии 2.1 читает только poetry 2.x
        if "$candidate" --version 2>/dev/null | grep -qE 'version 2\.'; then
            printf '%s' "$candidate"
            return 0
        fi
    done
    return 1
}

if POETRY="$(find_poetry)"; then
    log "Использую $POETRY ($("$POETRY" --version))"
else
    log "Ставлю poetry $POETRY_VERSION в $POETRY_HOME"
    python3 -m venv "$POETRY_HOME"
    "$POETRY_HOME/bin/pip" install --quiet --upgrade pip
    "$POETRY_HOME/bin/pip" install --quiet "poetry==$POETRY_VERSION"
    POETRY="$POETRY_HOME/bin/poetry"
fi

# --- 6. зависимости backend -------------------------------------------------

log "Ставлю зависимости backend по poetry.lock"
cd "$BACK_DIR"
POETRY_VIRTUALENVS_IN_PROJECT=true POETRY_NO_INTERACTION=1 "$POETRY" install --only main --no-root

# --- 7. сборка frontend -----------------------------------------------------

if [ "$SKIP_FRONTEND" -eq 1 ]; then
    log "Пропускаю сборку frontend, использую готовый dist"
else
    log "Собираю frontend (npm ci && npm run build)"
    cd "$FRONT_DIR"
    npm ci --silent
    npm run build
fi

# --- 8. .env ----------------------------------------------------------------

set_env() {
    local key="$1" value="$2" escaped
    escaped="$(printf '%s' "$value" | sed -e 's/[\/&]/\\&/g')"
    if grep -qE "^#? *$key=" "$ENV_FILE"; then
        sed -i -E "s|^#? *$key=.*|$key=$escaped|" "$ENV_FILE"
    else
        printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
    fi
}

if [ -f "$ENV_FILE" ]; then
    if [ "$MIGRATED_ENV" -eq 1 ]; then
        # правим только пути, которые вели в старый каталог: вынесенные наружу
        # (например, APP_DB_PATH=/var/lib/...) трогать нельзя
        log "Поправляю пути внутри перенесённого .env"
        sed -i -E "s|^(APP_DB_PATH=)$PREV_DIR/|\1$INSTALL_DIR/|; s|^(STATIC_DIR=)$PREV_DIR/|\1$INSTALL_DIR/|" "$ENV_FILE"
    else
        log "$ENV_FILE уже есть - меняю только то, что задано ключами"
    fi
    if [ "$LISTEN_SET" -eq 1 ]; then
        set_env GUNICORN_LISTEN "$LISTEN"
        log "GUNICORN_LISTEN=$LISTEN"
    fi
    if [ "$WORKERS_SET" -eq 1 ]; then
        set_env GUNICORN_WORKERS "$WORKERS"
        log "GUNICORN_WORKERS=$WORKERS"
    fi
else
    log "Создаю $ENV_FILE"
    cp "$BACK_DIR/.env.example" "$ENV_FILE"
    GENERATED_PASSWORD="$(openssl rand -base64 18 | tr -d '/+=' | cut -c1-16)"
    set_env SECRET_KEY "$(openssl rand -hex 32)"
    set_env BOOTSTRAP_ADMIN_PASSWORD "$GENERATED_PASSWORD"
    set_env APP_DB_PATH "$BACK_DIR/data/osips-ui.db"
    set_env STATIC_DIR "$FRONT_DIR/dist"
    set_env SERVE_STATIC true
    set_env DEBUG false
    set_env CORS_ORIGINS "[]"
    set_env GUNICORN_LISTEN "$LISTEN"
    set_env GUNICORN_WORKERS "$WORKERS"
fi

# --- 9. права ---------------------------------------------------------------

log "Выставляю права ($SERVICE_USER)"
mkdir -p "$BACK_DIR/data"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chmod 600 "$ENV_FILE"          # в .env лежит SECRET_KEY, которым шифруются пароли к БД opensips

# --- 10. systemd -------------------------------------------------------------

log "Ставлю unit $UNIT_FILE"
sed -e "s|__INSTALL_DIR__|$INSTALL_DIR|g" \
    -e "s|__SERVICE_USER__|$SERVICE_USER|g" \
    -e "s|__SERVICE_NAME__|$SERVICE_NAME|g" \
    "$INSTALL_DIR/install/osips-ui.service.template" > "$UNIT_FILE"
chmod 644 "$UNIT_FILE"

if [ "$WITH_SERVICE" -eq 0 ]; then
    log "Готово (--no-service): служба не запускалась"
    exit 0
fi

systemctl daemon-reload
systemctl enable "$SERVICE_NAME" >/dev/null 2>&1 || true
systemctl restart "$SERVICE_NAME"

# --- 11. проверка живости ---------------------------------------------------

port="${LISTEN##*:}"
health="http://127.0.0.1:$port/api/health"
ok=0
for _ in $(seq 1 30); do
    if python3 - "$health" <<'PY' >/dev/null 2>&1
import sys, urllib.request
sys.exit(0 if urllib.request.urlopen(sys.argv[1], timeout=2).status == 200 else 1)
PY
    then ok=1; break; fi
done

echo
if [ "$ok" -eq 1 ]; then
    log "Служба поднялась: $health отвечает"
else
    warn "Служба не ответила на $health - смотрите: journalctl -u $SERVICE_NAME -n 50"
fi

cat <<INFO

  Интерфейс:  http://$(hostname -I 2>/dev/null | awk '{print $1}'):$port/
  Swagger:    http://127.0.0.1:$port/docs
  Каталог:    $INSTALL_DIR
  Настройки:  $ENV_FILE
  Логи:       journalctl -u $SERVICE_NAME -f
  Управление: systemctl {status,restart,stop} $SERVICE_NAME
INFO

if [ -n "$PREV_DIR" ] && [ "$PREV_DIR" != "$INSTALL_DIR" ]; then
    cat <<INFO
  Прежний каталог $PREV_DIR оставлен на диске, данные из него уже перенесены.
  Убедитесь, что всё работает, и удалите его: rm -rf $PREV_DIR

INFO
fi

if [ -n "$GENERATED_PASSWORD" ]; then
    cat <<INFO
  Первый вход: admin / $GENERATED_PASSWORD
  Пароль сгенерирован сейчас и записан в .env. Смените его в разделе «Профиль»
  после первого входа - пользователь создаётся только когда таблица users пуста.

INFO
fi
