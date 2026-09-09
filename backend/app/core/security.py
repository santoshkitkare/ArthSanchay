"""Password hashing (Argon2id, FR-AUTH-2) and JWT encode/decode (FR-AUTH-3)."""
import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import get_settings

settings = get_settings()
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    try:
        return int(payload["sub"])
    except (KeyError, ValueError, TypeError):
        return None


def generate_refresh_token() -> str:
    """A high-entropy opaque token — stored server-side only as its hash (FR-AUTH-3)."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """SHA-256 for opaque, high-entropy tokens (refresh + password-reset). Argon2 is reserved
    for user-chosen passwords, which need its deliberate slowness; these tokens are already
    128+ bits of randomness, so a fast, deterministic hash is the right tool and lets lookup
    be a plain indexed equality check.
    """
    return sha256(token.encode("utf-8")).hexdigest()


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)
