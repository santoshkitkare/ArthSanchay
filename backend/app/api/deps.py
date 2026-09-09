"""Shared FastAPI dependencies: current-user resolution from the access-token cookie, and the
scenario-ownership check used by every scenario-scoped route (FR-AUTH-5 — 404, never 403, for
another user's scenario, so ids cannot be enumerated).
"""
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.core.security import decode_access_token
from app.db import get_db

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def get_current_user(
    access_token: str | None = Cookie(default=None, alias=ACCESS_COOKIE),
    db: Session = Depends(get_db),
) -> models.User:
    if access_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user_id = decode_access_token(access_token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    return user


def get_owned_scenario(
    scenario_id: int,
    db: Session,
    current_user: models.User,
) -> models.Scenario:
    scenario = db.get(models.Scenario, scenario_id)
    if scenario is None or scenario.user_id != current_user.id:
        # 404, not 403 (FR-AUTH-5): existence of another user's scenario is not revealed.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
    return scenario
