"""Клиент OpenSIPS Management Interface поверх http (модуль mi_http, JSON-RPC 2.0).

Проверено по исходникам OpenSIPS 3.6:
  dispatcher:     ds_list(partition?, full?), ds_set_state(state, group, address), ds_reload(partition?, inherit_state?)
  load_balancer:  lb_list(), lb_status(destination_id[, new_status]), lb_reload()
  usrloc:         ul_dump([brief])
"""

import logging
from typing import Any

import httpx

from ..config import settings
from ..core.crypto import decrypt
from ..db.models import OpensipsServer

logger = logging.getLogger("osips-ui")

_client: httpx.AsyncClient | None = None


class MIError(RuntimeError):
    """Ошибка обращения к MI: недоступен сервер либо opensips вернул error."""

    def __init__(self, message: str, *, code: int | None = None):
        super().__init__(message)
        self.code = code


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=settings.MI_TIMEOUT)
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def mi_url(server: OpensipsServer) -> str:
    host = server.mi_host or server.ip_address
    if not host or not server.mi_port:
        raise MIError(f"Для сервера '{server.name}' не настроен http MI (адрес и порт)")
    path = server.mi_path or "/mi"
    if not path.startswith("/"):
        path = "/" + path
    return f"http://{host}:{server.mi_port}{path}"


def has_mi(server: OpensipsServer) -> bool:
    return bool((server.mi_host or server.ip_address) and server.mi_port)


async def call(
    server: OpensipsServer,
    method: str,
    params: dict[str, Any] | None = None,
    *,
    timeout: float | None = None,
) -> Any:
    """Выполняет MI-команду и возвращает result. Бросает MIError.

    timeout переопределяет MI_TIMEOUT для тяжёлых команд (например, ul_dump на большой базе).
    """
    url = mi_url(server)
    payload: dict[str, Any] = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params:
        payload["params"] = params

    auth = None
    if server.mi_username:
        auth = httpx.BasicAuth(server.mi_username, decrypt(server.mi_password) or "")

    logger.debug("MI %s -> %s %s", server.name, method, params or {})
    request_timeout = settings.MI_TIMEOUT if timeout is None else timeout
    try:
        response = await get_client().post(url, json=payload, auth=auth, timeout=request_timeout)
    except httpx.TimeoutException as exc:
        raise MIError(f"{server.name}: {method} не ответил за {request_timeout:g} с") from exc
    except httpx.HTTPError as exc:
        raise MIError(f"{server.name}: MI недоступен ({exc.__class__.__name__}: {exc})") from exc

    if response.status_code >= 400:
        raise MIError(f"{server.name}: MI вернул HTTP {response.status_code}", code=response.status_code)

    try:
        data = response.json()
    except ValueError as exc:
        raise MIError(f"{server.name}: MI вернул не JSON") from exc

    if isinstance(data, dict) and data.get("error"):
        error = data["error"]
        message = error.get("message") if isinstance(error, dict) else str(error)
        code = error.get("code") if isinstance(error, dict) else None
        raise MIError(f"{server.name}: {method} -> {message}", code=code)

    # у команд-действий (ds_reload, ds_set_state) result это строка "OK"
    return data.get("result") if isinstance(data, dict) else data


async def ping(server: OpensipsServer) -> dict[str, Any]:
    """Проверка доступности MI (команда uptime есть всегда)."""
    try:
        result = await call(server, "uptime")
    except MIError as exc:
        return {"ok": False, "detail": str(exc)}

    # uptime отдаёт объект вида {"Now": ..., "Up since": ..., "Up time": ...}
    if isinstance(result, dict):
        uptime = result.get("Up time") or result.get("Up since")
        return {"ok": True, "detail": f"MI отвечает, uptime: {uptime}" if uptime else "MI отвечает"}
    return {"ok": True, "detail": str(result)}
