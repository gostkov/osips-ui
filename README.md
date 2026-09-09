# osips-ui — web-интерфейс управления серверами OpenSIPS

Управление кластером OpenSIPS: вывод нод из обслуживания (`dispatcher` / `load_balancer`),
правила трансляции (`dialplan`), медиасокеты (`rtpengine`), списки номеров (`userblacklist` /
`globalblacklist`), доверенные адреса (`permissions`), просмотр SIP-регистраций (`location`).
Везде одинаково: правка таблицы в БД плюс перезагрузка данных в память через MI.
Разграничение доступа — по настраиваемым ролям.

Проверено на схеме БД OpenSIPS **3.6** (`dev/init.sql`).

## Состав репозитория

```
osips-ui/
├── back-osips-ui/      backend: Python 3.11+, FastAPI, SQLAlchemy (async), SQLite для своих данных
├── front-osips-ui/     frontend: Vue 3 (Composition API) + Vuetify 3 + Pinia + Vue Router, сборка Vite
├── dev/init.sql        схема БД OpenSIPS для локального стенда
├── dev/seed.sql        тестовые данные для локальной разработки
└── docker-compose.yml  локальная разработка: MariaDB + backend + vite
```

В проде **nginx не нужен**: backend сам отдаёт собранный фронтенд (`STATIC_DIR`) и API на одном порту.

---

## 1. Возможности

### Роли и права

Роли **настраиваются в интерфейсе** (раздел «Роли и права», нужно право `users:manage`):
создать роль, задать ей набор разделов, переименовать, удалить. Перечень самих прав
фиксирован в коде — это то, что проверяют роутеры:

| Право | Что открывает |
|---|---|
| `servers:read` / `servers:write` | Просмотр реестра серверов / изменение |
| `dispatcher:read` / `dispatcher:write` | Таблица и состояние нод / переключение, правка, `ds_reload` |
| `lb:read` / `lb:write` | То же для load balancer |
| `dialplan:read` / `dialplan:write` | Правила `dialplan` и `dp_translate` / правка, `dp_reload` |
| `rtpengine:read` / `rtpengine:write` | Сокеты rtpengine и их состояние / правка, `rtpengine_enable`, `rtpengine_reload` |
| `blacklist:read` / `blacklist:write` | `userblacklist` и `globalblacklist` / правка, `reload_blacklist` |
| `address:read` / `address:write` | Таблица `address` модуля permissions / правка, `address_reload` |
| `sipregs:read` | SIP-регистрации |
| `users:manage` | Пользователи, роли и права |
| `audit:read` | Журнал действий |

При первом запуске создаются роли по умолчанию:

| Роль | Права |
|---|---|
| `admin` | все (**встроенная**: не редактируется и не удаляется) |
| `qa` | dispatcher, load balancer, dialplan и регистрации на чтение |
| `hardwares`, `reader` | серверы и SIP-регистрации на чтение |

Кроме `admin` все они обычные — переименовывайте, меняйте или удаляйте под свою схему.

**Защита от самоблокировки.** Встроенная роль `admin` всегда имеет полный доступ, что бы ни
лежало в БД; нельзя снять право «Пользователи и роли» со своей собственной роли и нельзя
перевести себя на роль без него. Роль, назначенную пользователям, удалить нельзя — сначала
переведите их на другую.

Матрица прав кешируется в каждом процессе на `RBAC_CACHE_TTL` секунд (по умолчанию 5): в своём
воркере правка видна сразу, в остальных — в пределах TTL.

### Серверы OpenSIPS

Сущность «сервер» описывает: имя, IP, адрес http MI (`ip:port` + путь, опционально basic-auth),
реквизиты БД (host, port, dbname, user, password) и партицию dispatcher. Несколько серверов
могут указывать на одну БД — пул подключений переиспользуется. Пароли шифруются в БД приложения
(Fernet, ключ выводится из `SECRET_KEY`).

### Dispatcher / Load balancer

* Содержимое таблиц `dispatcher` и `load_balancer` (вкладки), данные читаются из БД сервера.
* Колонка «Состояние» — switcher, состояние берётся из MI:
  * `dispatcher`: `ds_list` → `Active` (зелёный) / `Inactive` (серый) / `Probing` (красный);
  * `load_balancer`: `lb_list` → `enabled=yes` (зелёный), `enabled=no, auto-reenable=off` —
    выключен вручную (серый), `enabled=no, auto-reenable=on` — выключен пробингом (красный).
  * `н/д` — MI недоступен или ноды нет в выхлопе (например, строка добавлена, но `reload` ещё не сделан).
* Переключение switcher'а: `ds_set_state` (`a`/`i`) и `lb_status` (`new_status=1/0`).
* Добавление/редактирование/удаление строк — прямо в таблице БД.
* Кнопка «Обновить в памяти opensips» — `ds_reload` / `lb_reload`.

### Dialplan

Раздел `/dialplan` — таблица `dialplan` (модуль
[dialplan](https://opensips.org/docs/modules/3.6.x/dialplan.html)): пагинация, фильтр по набору
`dpid`, поиск по выражениям, переключатель «только включённые».

* `match_op`: `0` — равенство строк, `1` — регулярное выражение; флаг «без учёта регистра» — это
  бит 1 в `match_flags`.
* Замена: `subst_exp` + `repl_exp` (с обратными ссылками `\1`). Пустой `subst_exp` — `repl_exp`
  подставляется как есть, пустой `repl_exp` — строка остаётся прежней.
* `timerec` — окно действия правила (RFC 2445), `attrs` возвращается в скрипт вторым результатом.
* Кнопка «Обновить в памяти opensips» — `dp_reload` (без указания партиции перечитываются все).
* Кнопка «Проверить правило» — `dp_translate`: прогоняет строку через правила набора **в памяти
  opensips**, а не по таблице БД, и показывает результат с `attrs`.

Интерфейс работает с таблицей `dialplan` — именем по умолчанию. Если партиции в конфигурации
opensips смотрят в другие таблицы, правьте их через ту партицию, где они лежат.

### RTPEngine

Раздел `/rtpengine` — таблица `rtpengine` (модуль
[rtpengine](https://opensips.org/docs/modules/3.6.x/rtpengine.html)) плюс состояние сокетов из
`rtpengine_show`. Состояния те же три, что у dispatcher:

* зелёный — сокет работает;
* серый — выключен вручную (`rtpengine_enable ... 0`, `recheck_ticks` = `(unsigned)-1`);
* красный — выключил сам модуль после неудачного пинга, перепроверит через `recheck_ticks`.

Switcher вызывает `rtpengine_enable` — это состояние живёт только в памяти и в таблицу не пишется.
Кнопка «Обновить в памяти opensips» — `rtpengine_reload`, режим soft оставляет живые сокеты
нетронутыми. Reload работает, только если у модуля задан параметр `db_url`.

### Списки номеров

Раздел `/blacklist` — две вкладки модуля
[userblacklist](https://opensips.org/docs/modules/3.6.x/userblacklist.html):

* **userblacklist** — правила на конкретного абонента (`username`, `domain`, `prefix`). Модуль
  строит дерево префиксов запросом в БД **на каждый вызов** `check_user_blacklist()`, поэтому
  правки действуют сразу и reload не нужен.
* **globalblacklist** — общие правила по префиксам. Загружается в память при старте, поэтому
  после правки нужна кнопка «Обновить в памяти opensips» (`reload_blacklist`).

В обеих таблицах `whitelist=1` — разрешающее правило: оно снимает запрет, заданный более коротким
префиксом. В интерфейсе это отдельный фильтр «только запреты / только разрешения».

### Доверенные адреса

Раздел `/address` — таблица `address` модуля
[permissions](https://opensips.org/docs/modules/3.6.x/permissions.html): группа `grp`, адрес с
маской, порт, протокол, `pattern` и `context_info`.

Каждая строка сверяется с тем, что реально загружено в память opensips (`address_dump` +
`subnet_dump`), и получает отметку «загружен» либо «нужен reload». Отдельно показывается, сколько
записей есть в памяти, но нет в таблице — это признак того, что таблицу правили в обход
интерфейса. Кнопка «Обновить в памяти opensips» — `address_reload`.

### SIP-регистрации

Раздел `/sip-regs` (доступен всем ролям) показывает регистрации: абонент (`username@domain`),
`contact`, адрес из `received`/`socket`, user-agent и состояние регистрации. Переключатель
**«Из БД» / «Из памяти»** выбирает источник:

| Источник | Что читаем | Особенности |
|---|---|---|
| Из БД | таблица `location` | быстро, но заполнена только при `db_mode` 2/3; есть `last_modified` |
| Из памяти | MI `ul_dump` | актуально при любом `db_mode`; есть `state` (`CS_NEW`/`CS_SYNC`/`CS_DIRTY`) и ping-latency |

`ul_dump` выгружает всю память `usrloc` целиком и на большой базе отвечает долго, поэтому у него
отдельный таймаут `MI_DUMP_TIMEOUT` (по умолчанию 15 с) — обычный `MI_TIMEOUT` для него мал.
По истечении таймаута интерфейс покажет «ul_dump не ответил за 15 с». Кнопка источника, для
которого у сервера нет реквизитов (нет БД или не настроен http MI), недоступна.

Выбор источника запоминается в браузере. Строку можно развернуть — под ней остальные поля контакта (`call-id`, `cseq`, `q`,
`path`, `flags`/`cflags`, `methods`, `sip_instance`, `kv_store`, `attr`, время истечения и,
в зависимости от источника, `last_modified` либо `state`/ping-latency). Есть поиск (по номеру, `contact`, `received`, user-agent), фильтр
«только активные» и постраничный вывод (`SIPREGS_PAGE_SIZE`, по умолчанию 25).

Состояние в режиме «Из БД» считается по полю `expires` (абсолютный unix-time): `активна` — время
ещё не вышло, `истекла` — вышло либо контакт принудительно помечен истёкшим (`UL_EXPIRED_TIME`),
`постоянная` — `expires = 0` (такие контакты чистка usrloc не трогает). В режиме «Из памяти»
то же самое приходит из `ul_dump` уже разобранным: число секунд до истечения либо
`permanent` / `expired` / `deleted`.

> При `db_mode` 0/1 таблица `location` пустая — регистрации живут только в памяти OpenSIPS,
> и увидеть их можно лишь режимом «Из памяти».

### Прочее

* Журнал действий: кто, когда, на каком сервере и что менял (вход, переключение нод, reload,
  правки таблиц, пользователи).
* Задел под SSO: у пользователя есть поле `auth_provider` (`local` | `oidc`) и `external_id`;
  вход по паролю разрешён только при `auth_provider='local'`.

---

## 2. Требования к OpenSIPS

Для работы switcher'ов и кнопок reload на сервере должен быть включён http-интерфейс MI:

```
loadmodule "httpd.so"
modparam("httpd", "port", 8888)

loadmodule "mi_http.so"
# URL получится http://<ip>:8888/mi
```

Модули `dispatcher`, `load_balancer`, `dialplan`, `rtpengine`, `userblacklist` и `permissions`
должны быть настроены на ту же БД, что указана в карточке сервера — интерфейс правит те же
таблицы, что читает opensips. Разделы, модулей для которых на сервере нет, просто покажут пустые
таблицы, а кнопки reload вернут ошибку MI. Для сохранения состояния нод между перезапусками у `dispatcher` должен быть включён
`persistent_state` (по умолчанию включён) — состояние в колонку `state` пишет сам OpenSIPS,
интерфейс её не трогает.

Доступ к порту MI желательно ограничить фаерволом уровнем сети или закрыть basic-auth
(логин/пароль задаются в карточке сервера).

---

## 3. Локальная разработка

### Вариант А. Docker Compose (быстрый старт)

Поднимает MariaDB со схемой OpenSIPS и тестовыми данными, backend с автоперезагрузкой и vite:

```bash
cd osips-ui
docker compose up --build
```

* UI: http://localhost:5173
* API и Swagger: http://localhost:8000/docs
* MariaDB: `localhost:3306`, база `opensips`, пользователь `opensips` / `opensipsrw`
* Первый вход: `admin` / `admin`

Дальше в разделе «Серверы OpenSIPS» добавьте сервер, указав БД `opensips-db:3306` (или
`127.0.0.1:3306` при запуске backend вне контейнера) и адрес http MI вашего OpenSIPS.

Остановить и удалить данные: `docker compose down -v`.

### Вариант Б. Без Docker

Backend:

```bash
cd back-osips-ui
poetry install                           # venv и зависимости строго по poetry.lock
cp .env.example .env                     # правим SECRET_KEY, APP_DB_PATH, SERVE_STATIC=false
poetry run uvicorn app.main:app --reload --port 8000
```

Frontend (в отдельном терминале):

```bash
cd front-osips-ui
npm install
npm run dev            # http://localhost:5173, /api проксируется на 127.0.0.1:8000
```

Порт backend'а для прокси можно поменять: `VITE_API_TARGET=http://127.0.0.1:9000 npm run dev`.

### Тесты

```bash
cd back-osips-ui
PYTHONPATH=. .venv/bin/python -m pytest -q
```

---

## 4. Прод: сборка и запуск через systemd

Предполагается каталог `/opt/osips-ui`, пользователь `osips-ui`, порт `8000`.

```bash
# 1. код
sudo useradd -r -s /usr/sbin/nologin -d /opt/osips-ui osips-ui
sudo mkdir -p /opt/osips-ui && sudo chown osips-ui:osips-ui /opt/osips-ui
sudo -u osips-ui git clone <repo> /opt/osips-ui

# 2. фронтенд (нужен node >= 22; можно собрать на build-хосте и скопировать dist/)
cd /opt/osips-ui/front-osips-ui
npm ci
npm run build                     # результат в front-osips-ui/dist

# 3. бэкенд
cd /opt/osips-ui/back-osips-ui
pip install --user poetry                 # если poetry ещё нет
POETRY_VIRTUALENVS_IN_PROJECT=true poetry install --only main --no-root
cp .env.example .env
# ОБЯЗАТЕЛЬНО:
#   SECRET_KEY=$(openssl rand -hex 32)
#   BOOTSTRAP_ADMIN_PASSWORD=<надёжный пароль>
#   STATIC_DIR=/opt/osips-ui/front-osips-ui/dist
#   APP_DB_PATH=/opt/osips-ui/back-osips-ui/data/osips-ui.db
mkdir -p data
sudo chown -R osips-ui:osips-ui /opt/osips-ui

# 4. служба
sudo cp deploy/osips-ui.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now osips-ui
sudo systemctl status osips-ui
journalctl -u osips-ui -f
```

Интерфейс: `http://<host>:8000/`, Swagger: `http://<host>:8000/docs`.
Первый вход — логин/пароль из `BOOTSTRAP_ADMIN_*`; пользователь создаётся только когда таблица
`users` пуста. **Сразу смените пароль** в разделе «Профиль».

### Обновление версии

```bash
cd /opt/osips-ui && sudo -u osips-ui git pull
cd front-osips-ui && npm ci && npm run build
cd ../back-osips-ui && POETRY_VIRTUALENVS_IN_PROJECT=true poetry install --only main --no-root
sudo systemctl restart osips-ui
```

### Если нужен HTTPS

Поставьте перед приложением любой reverse-proxy (nginx, traefik) и пробросьте
`X-Forwarded-For` — IP клиента в журнале действий берётся из этого заголовка.
При проксировании на подпуть задайте `ROOT_PATH=/osips-ui`.

---

## 5. Конфигурация backend (`back-osips-ui/.env`)

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `SECRET_KEY` | — | Подпись JWT и шифрование секретов. **Смена делает сохранённые пароли БД нечитаемыми** |
| `RBAC_CACHE_TTL` | `5` | Сколько секунд воркер держит матрицу прав в памяти |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `720` | Время жизни токена |
| `APP_DB_PATH` | `back-osips-ui/data/osips-ui.db` | SQLite приложения |
| `BOOTSTRAP_ADMIN_USERNAME` / `_PASSWORD` | `admin` / `admin` | Первый администратор |
| `STATIC_DIR` | `../front-osips-ui/dist` | Каталог собранного фронтенда |
| `SERVE_STATIC` | `true` | Отдавать ли статику из backend |
| `CORS_ORIGINS` | `["http://localhost:5173", ...]` | Нужен только для vite dev; в проде `[]` |
| `MI_TIMEOUT` | `5` | Таймаут http MI, сек |
| `MI_DUMP_TIMEOUT` | `15` | Отдельный таймаут `ul_dump`, сек |
| `OPENSIPS_DB_POOL_SIZE` | `3` | Размер пула на каждую БД OpenSIPS |
| `DIALPLAN_PAGE_SIZE` | `25` | Записей на странице dialplan |
| `BLACKLIST_PAGE_SIZE` | `25` | Записей на странице списков номеров |
| `SIPREGS_PAGE_SIZE` | `25` | Записей на странице SIP-регистраций |
| `DEBUG` | `false` | Подробный лог и SQL-echo |
| `GUNICORN_LISTEN` / `_WORKERS` / `_LOGLEVEL` | `0.0.0.0:8000` / `2` / `info` | Параметры gunicorn |

---

## 6. Основные эндпоинты

| Метод и путь | Права | Назначение |
|---|---|---|
| `POST /api/auth/login` | — | Вход, выдача JWT |
| `GET /api/auth/me` | любой | Профиль и список прав |
| `GET/POST/PUT/DELETE /api/users` | `users:manage` | Пользователи и роли |
| `GET/POST/PUT/DELETE /api/servers` | чтение — все, запись — `servers:write` | Реестр серверов |
| `POST /api/servers/{id}/check` | любой | Проверка доступности БД и MI |
| `GET /api/servers/{id}/dispatcher` | `dispatcher:read` | Таблица + состояние из `ds_list` |
| `POST /api/servers/{id}/dispatcher/{row}/state` | `dispatcher:write` | `ds_set_state` |
| `POST /api/servers/{id}/dispatcher/reload` | `dispatcher:write` | `ds_reload` |
| `GET /api/servers/{id}/loadbalancer` | `lb:read` | Таблица + состояние из `lb_list` |
| `POST /api/servers/{id}/loadbalancer/{row}/status` | `lb:write` | `lb_status` |
| `POST /api/servers/{id}/loadbalancer/reload` | `lb:write` | `lb_reload` |
| `GET/POST/PUT/DELETE /api/servers/{id}/dialplan` | `dialplan:read` / `dialplan:write` | Правила dialplan |
| `POST /api/servers/{id}/dialplan/reload` | `dialplan:write` | `dp_reload` |
| `POST /api/servers/{id}/dialplan/translate` | `dialplan:read` | `dp_translate` |
| `GET/POST/PUT/DELETE /api/servers/{id}/rtpengine` | `rtpengine:read` / `rtpengine:write` | Сокеты + состояние из `rtpengine_show` |
| `POST /api/servers/{id}/rtpengine/{row}/enabled` | `rtpengine:write` | `rtpengine_enable` |
| `POST /api/servers/{id}/rtpengine/reload` | `rtpengine:write` | `rtpengine_reload` |
| `GET/POST/PUT/DELETE /api/servers/{id}/blacklist/{user\|global}` | `blacklist:read` / `blacklist:write` | `userblacklist` и `globalblacklist` |
| `POST /api/servers/{id}/blacklist/reload` | `blacklist:write` | `reload_blacklist` |
| `GET/POST/PUT/DELETE /api/servers/{id}/address` | `address:read` / `address:write` | Таблица `address` + дамп из памяти |
| `POST /api/servers/{id}/address/reload` | `address:write` | `address_reload` |
| `GET /api/servers/{id}/sip-regs` | `sipregs:read` | Регистрации: `source=db` (`location`) или `source=mi` (`ul_dump`) |
| `GET/POST /api/roles` | `users:manage` | Роли и их права |
| `PUT/DELETE /api/roles/{id}` | `users:manage` | Изменение и удаление роли |
| `GET /api/roles/permissions` | `users:manage` | Каталог прав по разделам |
| `GET /api/audit` | `audit:read` | Журнал действий |

Полное описание — в Swagger `/docs`.

---

## 7. Диагностика

| Симптом | Причина и что делать |
|---|---|
| Состояние нод «н/д», предупреждение над таблицей | Недоступен http MI: проверьте `httpd`/`mi_http` в OpenSIPS и порт в карточке сервера. Кнопка «проверить» в разделе «Серверы» покажет текст ошибки |
| `502` и «ошибка запроса к БД» | Неверные реквизиты БД или нет сетевого доступа. Проверьте кнопкой «проверить» |
| «Не удалось расшифровать секрет: SECRET_KEY изменился?» | Сменили `SECRET_KEY` — введите пароли БД и токены заново в карточках серверов |
| Новая строка есть в таблице, но состояние «н/д» | OpenSIPS ещё не знает о ней — нажмите «Обновить в памяти opensips» |
| После `ds_reload` ноды снова активны | Так работает OpenSIPS: `ds_reload` без `inherit_state` сбрасывает состояния к значениям из БД |
| Не пускает после смены пароля | Токен привязан к пользователю, а не к паролю; перелогиньтесь |

---

## 8. Лицензия

Код проекта распространяется по лицензии [MIT](LICENSE).

Файл `dev/init.sql` — схема БД из дистрибутива [OpenSIPS](https://github.com/OpenSIPS/opensips)
и распространяется на условиях его собственной лицензии (GPL-2.0+). Он лежит в репозитории
только для того, чтобы поднять локальный стенд одной командой; сам OpenSIPS в состав проекта
не входит.
