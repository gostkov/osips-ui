"""Права доступа и роли.

Перечень прав (Perm) фиксирован в коде - именно их проверяют роутеры. Состав ролей,
наоборот, динамический: роли лежат в БД приложения и настраиваются в интерфейсе
(раздел «Роли»). Встроенная роль admin всегда имеет все права, её нельзя изменить или
удалить - иначе интерфейс можно было бы заблокировать, сняв с себя users:manage.

Матрица «роль -> права» читается через app/services/rbac.py (с кешем).
"""

from enum import StrEnum


class Perm(StrEnum):
    # реестр opensips-серверов
    SERVERS_READ = "servers:read"
    SERVERS_WRITE = "servers:write"
    # dispatcher / load_balancer
    DISPATCHER_READ = "dispatcher:read"
    DISPATCHER_WRITE = "dispatcher:write"
    LB_READ = "lb:read"
    LB_WRITE = "lb:write"
    # dialplan
    DIALPLAN_READ = "dialplan:read"
    DIALPLAN_WRITE = "dialplan:write"
    # rtpengine
    RTPENGINE_READ = "rtpengine:read"
    RTPENGINE_WRITE = "rtpengine:write"
    # списки номеров (userblacklist / globalblacklist)
    BLACKLIST_READ = "blacklist:read"
    BLACKLIST_WRITE = "blacklist:write"
    # доверенные адреса (permissions, таблица address)
    ADDRESS_READ = "address:read"
    ADDRESS_WRITE = "address:write"
    # SIP-регистрации
    SIPREGS_READ = "sipregs:read"
    # пользователи и аудит
    USERS_MANAGE = "users:manage"
    AUDIT_READ = "audit:read"


# встроенная роль с полным доступом: не редактируется и не удаляется
ADMIN_ROLE = "admin"

# сгруппированный каталог прав для интерфейса (порядок как в меню)
PERM_GROUPS: list[dict] = [
    {
        "section": "Серверы OpenSIPS",
        "permissions": [
            {"value": Perm.SERVERS_READ, "title": "Просмотр списка серверов"},
            {"value": Perm.SERVERS_WRITE, "title": "Добавление и изменение серверов"},
        ],
    },
    {
        "section": "Dispatcher",
        "permissions": [
            {"value": Perm.DISPATCHER_READ, "title": "Просмотр таблицы и состояния нод"},
            {"value": Perm.DISPATCHER_WRITE, "title": "Переключение нод, правка таблицы, ds_reload"},
        ],
    },
    {
        "section": "Load balancer",
        "permissions": [
            {"value": Perm.LB_READ, "title": "Просмотр таблицы и состояния нод"},
            {"value": Perm.LB_WRITE, "title": "Переключение нод, правка таблицы, lb_reload"},
        ],
    },
    {
        "section": "Dialplan",
        "permissions": [
            {"value": Perm.DIALPLAN_READ, "title": "Просмотр правил и dp_translate"},
            {"value": Perm.DIALPLAN_WRITE, "title": "Правка правил, dp_reload"},
        ],
    },
    {
        "section": "RTPEngine",
        "permissions": [
            {"value": Perm.RTPENGINE_READ, "title": "Просмотр сокетов и их состояния"},
            {"value": Perm.RTPENGINE_WRITE, "title": "Включение/выключение сокетов, правка таблицы, rtpengine_reload"},
        ],
    },
    {
        "section": "Списки номеров",
        "permissions": [
            {"value": Perm.BLACKLIST_READ, "title": "Просмотр userblacklist и globalblacklist"},
            {"value": Perm.BLACKLIST_WRITE, "title": "Правка списков, reload_blacklist"},
        ],
    },
    {
        "section": "Доверенные адреса",
        "permissions": [
            {"value": Perm.ADDRESS_READ, "title": "Просмотр таблицы address и дампа из памяти"},
            {"value": Perm.ADDRESS_WRITE, "title": "Правка таблицы, address_reload"},
        ],
    },
    {
        "section": "SIP-регистрации",
        "permissions": [
            {"value": Perm.SIPREGS_READ, "title": "Просмотр регистраций"},
        ],
    },
    {
        "section": "Администрирование",
        "permissions": [
            {"value": Perm.USERS_MANAGE, "title": "Пользователи и роли"},
            {"value": Perm.AUDIT_READ, "title": "Журнал действий"},
        ],
    },
]

# роли, которые создаются при первом запуске; кроме admin все они обычные - их можно
# переименовать, изменить или удалить в интерфейсе
DEFAULT_ROLES: list[dict] = [
    {
        "slug": ADMIN_ROLE,
        "title": "Администратор",
        "description": "Полный доступ ко всем разделам. Встроенная роль, права не меняются.",
        "is_builtin": True,
        "permissions": list(Perm),
    },
    {
        "slug": "qa",
        "title": "QA",
        "description": "Dispatcher, load balancer, dialplan и регистрации только на чтение.",
        "is_builtin": False,
        "permissions": [
            Perm.SERVERS_READ,
            Perm.DISPATCHER_READ,
            Perm.LB_READ,
            Perm.DIALPLAN_READ,
            Perm.SIPREGS_READ,
        ],
    },
    {
        "slug": "hardwares",
        "title": "Оборудование",
        "description": "Просмотр SIP-регистраций.",
        "is_builtin": False,
        "permissions": [Perm.SERVERS_READ, Perm.SIPREGS_READ],
    },
    {
        "slug": "reader",
        "title": "Наблюдатель",
        "description": "Просмотр SIP-регистраций.",
        "is_builtin": False,
        "permissions": [Perm.SERVERS_READ, Perm.SIPREGS_READ],
    },
]
