"""Точка входа backend'а osips-ui.

В проде это же приложение отдаёт собранный фронтенд (STATIC_DIR), отдельный nginx не нужен.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .api import address, audit, auth, blacklist, dialplan, dispatcher, loadbalancer, roles, rtpengine, servers, sipregs, users
from .config import settings
from .db.session import init_db
from .services.mi import MIError, close_client
from .services.opensips_db import OpensipsDBError, dispose_all

logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("osips-ui")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Инициализация БД приложения: %s", settings.APP_DB_PATH)
    await init_db()
    yield
    await close_client()
    await dispose_all()
    logger.info("Остановка приложения")


app = FastAPI(
    title="osips-ui API",
    description="Web-интерфейс управления серверами OpenSIPS: dispatcher, load_balancer, dialplan, rtpengine, списки номеров, доверенные адреса",
    version=settings.APP_VERSION,
    root_path=settings.ROOT_PATH,
    lifespan=lifespan,
)

if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.exception_handler(MIError)
async def mi_error_handler(request: Request, exc: MIError) -> JSONResponse:
    logger.warning("MI error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content={"detail": str(exc)})


@app.exception_handler(OpensipsDBError)
async def db_error_handler(request: Request, exc: OpensipsDBError) -> JSONResponse:
    logger.warning("opensips DB error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content={"detail": str(exc)})


@app.get("/api/health", tags=["service"], summary="Проверка живости")
async def health() -> dict:
    return {"status": "ok", "version": settings.APP_VERSION}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(servers.router)
app.include_router(dispatcher.router)
app.include_router(loadbalancer.router)
app.include_router(dialplan.router)
app.include_router(rtpengine.router)
app.include_router(blacklist.router)
app.include_router(address.router)
app.include_router(sipregs.router)
app.include_router(audit.router)


static_dir = Path(settings.STATIC_DIR)
if settings.SERVE_STATIC and static_dir.is_dir():
    logger.info("Раздача статики из %s", static_dir)
    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # response_model=None обязателен: возвращаем Response, а не pydantic-модель
    @app.get("/{full_path:path}", include_in_schema=False, response_model=None)
    async def spa(full_path: str) -> Response:
        if full_path.startswith("api/"):
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not Found"})
        candidate = (static_dir / full_path).resolve()
        # отдаём реальный файл, если он есть, иначе index.html - роутинг разруливает Vue Router
        if full_path and candidate.is_file() and candidate.is_relative_to(static_dir.resolve()):
            return FileResponse(candidate)
        return FileResponse(static_dir / "index.html")

else:
    logger.warning("Статика не найдена в %s - фронтенд не собран или запущен отдельно (vite dev)", static_dir)
