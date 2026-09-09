# install

Два способа развернуть osips-ui в проде. Оба ставят одно приложение: backend отдаёт
и API, и собранный фронтенд на одном порту, отдельный nginx не нужен.

| Файл | Зачем |
|---|---|
| `install.sh` | установка на хост под systemd (вариант А) |
| `uninstall.sh` | снятие службы, с `--purge` — вместе с каталогом и базой |
| `osips-ui.service.template` | шаблон unit-файла, плейсхолдеры подставляет `install.sh` |
| `Dockerfile` | прод-образ: фронтенд + backend + gunicorn (вариант Б) |
| `docker-compose.prod.yml` | запуск этого образа |
| `.env.docker.example` | переменные для compose, копируется в `install/.env` |

## Вариант А. systemd

```bash
git clone git@github.com:gostkov/osips-ui.git && cd osips-ui
sudo install/install.sh
```

Скрипт создаёт системного пользователя `osips-ui`, копирует код в `/opt/osips-ui`,
ставит зависимости по `poetry.lock`, собирает фронтенд, генерирует `.env`
(со случайными `SECRET_KEY` и паролем администратора), кладёт unit и запускает службу.
Пароль первого входа печатается в конце.

Unit ужесточён: каталог установки только на чтение (кроме `data/`), нет capabilities,
`SystemCallFilter=@system-service`, доступ к сети ограничен `AF_UNIX`/`AF_INET`/`AF_INET6`,
sysctl, cgroups, `/proc/kcore` и чужие процессы недоступны — `systemd-analyze security osips-ui`
показывает 1.5 (OK). После правок шаблона стоит прогонять эту же команду.

Ключи и переменные:

```bash
sudo install/install.sh --install-dir /srv/osips-ui --listen 127.0.0.1:8080 --workers 4
sudo install/install.sh --skip-frontend           # dist собран заранее, node на хосте не нужен
sudo install/install.sh --no-service              # только разложить файлы, systemd не трогать
sudo install/install.sh --help                    # все ключи
```

Ключи: `-d/--install-dir`, `-u/--user`, `-n/--service-name`, `-l/--listen`, `-w/--workers`,
`--skip-frontend`, `--no-service`. Те же значения читаются из переменных окружения
`INSTALL_DIR`, `SERVICE_USER`, `SERVICE_NAME`, `LISTEN`, `WORKERS`, `POETRY_HOME`,
`POETRY_VERSION`, но ключ важнее.

Смена `--install-dir` на уже установленной системе — это переезд: служба останавливается,
`.env` и база переносятся на новое место, пути внутри `.env` правятся, служба поднимается
оттуда. Старый каталог остаётся на диске, удалить его нужно вручную.
`uninstall.sh` без ключей сам берёт каталог из unit-файла, так что `--purge` удалит
именно тот, с которым работала служба.

Повторный запуск = обновление: код и зависимости обновятся, `.env` и база останутся
нетронутыми. Обновление из репозитория:

```bash
git pull && sudo install/install.sh
```

## Вариант Б. Docker

```bash
cd install
cp .env.docker.example .env
$EDITOR .env                      # SECRET_KEY (openssl rand -hex 32) и BOOTSTRAP_ADMIN_PASSWORD
docker compose -f docker-compose.prod.yml up -d --build
```

База приложения лежит в томе `osips-ui-data` и переживает пересоздание контейнера.
Обновление: `git pull && docker compose -f docker-compose.prod.yml up -d --build`.

Внешние БД OpenSIPS и MI в compose не входят: серверы добавляются в интерфейсе,
контейнеру нужен только сетевой доступ до них (MySQL/MariaDB и http MI).
