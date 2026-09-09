"""Shared test fixtures.

The engine/solver tests (`test_engine_*`, `test_solver.py`) are pure-function tests and need
nothing here. The API tests (`test_api_*`) get a `client` fixture: a real `app.main.app` with its
`get_db` dependency overridden to a fresh, isolated in-memory-per-test SQLite engine — the
standard FastAPI testing pattern, so no module needs to be reloaded and the app's routes (bound to
`app.api.deps.get_db` at import time) still resolve correctly.
"""
import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Must be set before anything imports app.config (its Settings are cached via lru_cache).
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("SKIP_MIGRATIONS", "1")

XLSX_PATH = BACKEND_DIR.parent / "Retirement_Planner_Calculator_05102025.xlsx"


@pytest.fixture()
def client():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    import app.models  # noqa: F401  (registers every model on Base.metadata)
    from app.api import deps
    from app.db import Base
    from app.main import app

    # StaticPool: a single shared connection, so every session sees the same in-memory database
    # (plain SQLite in-memory otherwise hands out a fresh empty database per connection).
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def override_get_db():
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[deps.get_db] = override_get_db

    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    engine.dispose()
