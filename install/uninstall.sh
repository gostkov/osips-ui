#!/usr/bin/env bash
#
# Снятие osips-ui с хоста.
#
#   sudo install/uninstall.sh           # остановить и убрать службу, файлы и база остаются
#   sudo install/uninstall.sh --purge   # + удалить каталог установки и системного пользователя
#
# Ключи:
#   -d, --install-dir DIR   каталог установки (по умолчанию берётся из unit-файла)
#   -u, --user USER         системный пользователь службы (osips-ui)
#   -n, --service-name NAME имя службы systemd (osips-ui)
#       --purge             удалить каталог установки, базу и пользователя
#   -y, --yes               не спрашивать подтверждения при --purge
#
# То же можно задать переменными: INSTALL_DIR, SERVICE_USER, SERVICE_NAME.

set -euo pipefail

SERVICE_USER="${SERVICE_USER:-osips-ui}"
SERVICE_NAME="${SERVICE_NAME:-osips-ui}"
INSTALL_DIR="${INSTALL_DIR:-}"

PURGE=0
ASSUME_YES=0

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

need_value() { [ -n "${2:-}" ] || die "Ключу $1 нужно значение"; }

while [ $# -gt 0 ]; do
    case "$1" in
        -d|--install-dir)  need_value "$1" "${2:-}"; INSTALL_DIR="$2"; shift ;;
        -u|--user)         need_value "$1" "${2:-}"; SERVICE_USER="$2"; shift ;;
        -n|--service-name) need_value "$1" "${2:-}"; SERVICE_NAME="$2"; shift ;;
        --purge) PURGE=1 ;;
        -y|--yes) ASSUME_YES=1 ;;
        -h|--help) sed -n '2,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) die "Неизвестный аргумент: $1" ;;
    esac
    shift
done

[ "$(id -u)" -eq 0 ] || die "Запускать от root"

UNIT_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# каталог установки берём из unit-файла - там он гарантированно тот, с которым служба работала
if [ -z "$INSTALL_DIR" ] && [ -f "$UNIT_FILE" ]; then
    INSTALL_DIR="$(sed -n 's|^WorkingDirectory=\(.*\)/back-osips-ui[[:space:]]*$|\1|p' "$UNIT_FILE" | head -1)"
fi
INSTALL_DIR="${INSTALL_DIR:-/opt/osips-ui}"

if systemctl list-unit-files "$SERVICE_NAME.service" >/dev/null 2>&1; then
    log "Останавливаю службу $SERVICE_NAME"
    systemctl disable --now "$SERVICE_NAME" >/dev/null 2>&1 || true
fi
if [ -f "$UNIT_FILE" ]; then
    log "Удаляю $UNIT_FILE"
    rm -f "$UNIT_FILE"
    systemctl daemon-reload
fi

if [ "$PURGE" -eq 0 ]; then
    log "Служба снята. Каталог $INSTALL_DIR и база приложения оставлены."
    echo "    Полное удаление вместе с данными: sudo $0 --purge"
    exit 0
fi

db_path="$INSTALL_DIR/back-osips-ui/data"
if [ "$ASSUME_YES" -eq 0 ]; then
    echo "Будет безвозвратно удалено:"
    echo "  $INSTALL_DIR (включая базу приложения в $db_path: пользователи, роли, реестр серверов, журнал)"
    echo "  системный пользователь $SERVICE_USER"
    read -r -p "Продолжить? [y/N] " answer
    case "$answer" in [yY]|[yY][eE][sS]) ;; *) die "Отменено" ;; esac
fi

if [ -d "$INSTALL_DIR" ]; then
    log "Удаляю $INSTALL_DIR"
    rm -rf "$INSTALL_DIR"
fi
if id -u "$SERVICE_USER" >/dev/null 2>&1; then
    log "Удаляю пользователя $SERVICE_USER"
    userdel "$SERVICE_USER" || true
fi
log "Готово"
