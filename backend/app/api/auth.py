"""Authentication routes — FR-AUTH-1 through FR-AUTH-7.

Access and refresh tokens are delivered as HttpOnly cookies (FR-AUTH-4); the SPA never reads them
from JavaScript. Refresh tokens are stored server-side only as a SHA-256 hash and rotated on every
use (FR-AUTH-3). Login is rate-limited per email (FR-AUTH-7). Password reset (FR-AUTH-6) is real
end-to-end except delivery, which is stubbed to a log line — see services/email.py.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import models
from app.api.deps import ACCESS_COOKIE, REFRESH_COOKIE, get_current_user, get_db
from app.config import get_settings
from app.core.rate_limit import get_login_rate_limiter
from app.core.timeutils import as_aware_utc
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    generate_reset_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    UserOut,
)
from app.services.email import send_reset_email

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        max_age=settings.access_token_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=settings.refresh_token_days * 24 * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


def _issue_refresh_token(db: Session, user_id: int) -> str:
    token = generate_refresh_token()
    record = models.RefreshToken(
        user_id=user_id,
        token_hash=hash_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days),
    )
    db.add(record)
    db.commit()
    return token


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)) -> models.User:
    existing = db.query(models.User).filter(models.User.email == payload.email.lower()).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    user = models.User(email=payload.email.lower(), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    access = create_access_token(user.id)
    refresh = _issue_refresh_token(db, user.id)
    _set_auth_cookies(response, access, refresh)
    return user


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> models.User:
    limiter = get_login_rate_limiter()
    allowed, retry_seconds = limiter.check(payload.email)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed attempts. Try again in {retry_seconds} seconds.",
        )

    user = db.query(models.User).filter(models.User.email == payload.email.lower()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        limiter.record_failure(payload.email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    limiter.record_success(payload.email)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    access = create_access_token(user.id)
    refresh = _issue_refresh_token(db, user.id)
    _set_auth_cookies(response, access, refresh)
    return user


@router.post("/refresh", response_model=UserOut)
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    db: Session = Depends(get_db),
) -> models.User:
    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    token_hash = hash_token(refresh_token)
    record = db.query(models.RefreshToken).filter(models.RefreshToken.token_hash == token_hash).first()
    now = datetime.now(timezone.utc)
    if record is None or record.revoked_at is not None or as_aware_utc(record.expires_at) < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalid or expired")

    record.revoked_at = now  # rotate: this token is single-use
    db.commit()

    user = db.get(models.User, record.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account no longer exists")

    access = create_access_token(user.id)
    new_refresh = _issue_refresh_token(db, user.id)
    _set_auth_cookies(response, access, new_refresh)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    db: Session = Depends(get_db),
) -> None:
    if refresh_token is not None:
        token_hash = hash_token(refresh_token)
        record = db.query(models.RefreshToken).filter(models.RefreshToken.token_hash == token_hash).first()
        if record is not None and record.revoked_at is None:
            record.revoked_at = datetime.now(timezone.utc)
            db.commit()
    _clear_auth_cookies(response)


@router.get("/me", response_model=UserOut)
def me(current_user: models.User = Depends(get_current_user)) -> models.User:
    return current_user


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> dict:
    user = db.query(models.User).filter(models.User.email == payload.email.lower()).first()
    if user is not None:
        token = generate_reset_token()
        record = models.PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        db.add(record)
        db.commit()
        send_reset_email(user.email, f"/reset-password?token={token}")
    # Same response whether or not the email exists, so login emails cannot be enumerated.
    return {"detail": "If that email exists, a reset link has been sent."}


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)) -> None:
    token_hash = hash_token(payload.token)
    record = db.query(models.PasswordResetToken).filter(models.PasswordResetToken.token_hash == token_hash).first()
    now = datetime.now(timezone.utc)
    if record is None or record.used_at is not None or as_aware_utc(record.expires_at) < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset link is invalid or has expired")

    user = db.get(models.User, record.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset link is invalid or has expired")

    user.password_hash = hash_password(payload.new_password)
    record.used_at = now
    # Invalidate every existing session — a password reset should end all of them.
    for rt in db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == user.id, models.RefreshToken.revoked_at.is_(None)
    ):
        rt.revoked_at = now
    db.commit()
