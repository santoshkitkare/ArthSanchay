"""The anonymous, no-login calculator (PRD.md §8.1 landing page). Rate-limited by IP since it
requires no account (§7's `/api/project/anonymous` row).
"""
import threading
import time

from fastapi import APIRouter, HTTPException, Request, status

from app.core.engine import project
from app.schemas.projection import AnonymousProjectionRequest, ProjectionOut
from app.services.projection_service import engine_result_to_schema, inputs_in_to_engine

router = APIRouter(prefix="/api/project", tags=["projection"])

_ANON_LIMIT = 30
_ANON_WINDOW_SECONDS = 60
_anon_hits: dict[str, list[float]] = {}
_anon_lock = threading.Lock()


def _rate_limit_ip(ip: str) -> None:
    now = time.time()
    with _anon_lock:
        hits = [t for t in _anon_hits.get(ip, []) if now - t < _ANON_WINDOW_SECONDS]
        if len(hits) >= _ANON_LIMIT:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")
        hits.append(now)
        _anon_hits[ip] = hits


@router.post("/anonymous", response_model=ProjectionOut)
def project_anonymous(payload: AnonymousProjectionRequest, request: Request) -> ProjectionOut:
    client_ip = request.client.host if request.client else "unknown"
    _rate_limit_ip(client_ip)

    inp = inputs_in_to_engine(payload.inputs, payload.dependents, payload.goals, payload.income_streams)
    result = project(inp)
    return engine_result_to_schema(result, inp)
