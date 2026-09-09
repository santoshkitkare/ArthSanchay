"""SQLAlchemy engine/session setup. SQLite does not enforce foreign keys unless told to
per-connection (PRD.md §6), so that PRAGMA is issued on every new DBAPI connection.
"""
import os
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

_connect_args = {}
if settings.database_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
    # Ensure the directory for a file-based SQLite DB exists before connecting.
    if ":///" in settings.database_url and settings.database_url != "sqlite:///:memory:":
        path = settings.database_url.split("sqlite:///", 1)[-1]
        if path and path != ":memory:":
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)

engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001, ARG001
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
