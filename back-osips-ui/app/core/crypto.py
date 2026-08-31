"""Шифрование секретов, которые лежат в БД приложения (пароли от БД opensips, токены API).

Ключ Fernet детерминированно выводится из SECRET_KEY, отдельный ключ хранить не нужно.
Смена SECRET_KEY делает ранее сохранённые секреты нечитаемыми - их нужно будет ввести заново.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from ..config import settings

_PREFIX = "enc:"


def _fernet() -> Fernet:
    key = hashlib.sha256(f"osips-ui-secret-box:{settings.SECRET_KEY}".encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt(value: str | None) -> str | None:
    if value is None or value == "":
        return value
    return _PREFIX + _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt(value: str | None) -> str | None:
    if value is None or value == "":
        return value
    if not value.startswith(_PREFIX):
        # значение записано до включения шифрования - возвращаем как есть
        return value
    try:
        return _fernet().decrypt(value[len(_PREFIX) :].encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Не удалось расшифровать секрет: SECRET_KEY изменился?") from exc
