"""FastAPI application factory — router registration, CORS, DB migrations on startup, and the
production static-SPA fallback (PRD.md §10.3: one process serves both the API and the built
React app).
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth, health, projection, scenarios
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("app")

BACKEND_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BACKEND_DIR / "app" / "static"


def _run_migrations() -> None:
    alembic_ini = BACKEND_DIR / "alembic.ini"
    if not alembic_ini.exists():
        logger.warning("alembic.ini not found at %s; skipping migrations", alembic_ini)
        return
    cfg = Config(str(alembic_ini))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.environ.get("SKIP_MIGRATIONS") != "1":
        _run_migrations()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="ArthSanchay API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(scenarios.router)
    app.include_router(projection.router)

    index_html = STATIC_DIR / "index.html"
    assets_dir = STATIC_DIR / "assets"
    if index_html.exists():
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}")
        async def spa_fallback(full_path: str):  # noqa: ANN201, ARG001
            return FileResponse(index_html)

    return app


app = create_app()
