"""In-memory sliding-window rate limiter for login attempts (FR-AUTH-7).

Deliberately simple: a dict keyed by (lower-cased) email, guarded by a lock. This is process-
local — it resets on restart and does not coordinate across multiple processes/workers. That is
an acceptable limitation for the single-process SQLite deployment this app targets (PRD.md
§10.3); a multi-process deployment would need a shared store (e.g. Redis) instead.
"""
import threading
from datetime import datetime, timedelta, timezone


class LoginRateLimiter:
    def __init__(self, max_attempts: int, window_minutes: int) -> None:
        self._max_attempts = max_attempts
        self._window = timedelta(minutes=window_minutes)
        self._failures: dict[str, list[datetime]] = {}
        self._strikes: dict[str, int] = {}
        self._lock = threading.Lock()

    def _key(self, email: str) -> str:
        return email.strip().lower()

    def check(self, email: str) -> tuple[bool, int]:
        """Returns (allowed, seconds_until_retry). seconds_until_retry is 0 when allowed."""
        key = self._key(email)
        now = datetime.now(timezone.utc)
        with self._lock:
            attempts = [t for t in self._failures.get(key, []) if now - t < self._window]
            self._failures[key] = attempts
            if len(attempts) < self._max_attempts:
                return True, 0
            # Exponential lockout: each additional cluster of failures doubles the wait,
            # measured from the most recent failure.
            strikes = self._strikes.get(key, 0)
            lockout = self._window * (2**strikes)
            retry_at = attempts[-1] + lockout
            remaining = (retry_at - now).total_seconds()
            if remaining <= 0:
                return True, 0
            return False, int(remaining) + 1

    def record_failure(self, email: str) -> None:
        key = self._key(email)
        now = datetime.now(timezone.utc)
        with self._lock:
            attempts = [t for t in self._failures.get(key, []) if now - t < self._window]
            attempts.append(now)
            self._failures[key] = attempts
            if len(attempts) >= self._max_attempts:
                self._strikes[key] = self._strikes.get(key, 0) + 1

    def record_success(self, email: str) -> None:
        key = self._key(email)
        with self._lock:
            self._failures.pop(key, None)
            self._strikes.pop(key, None)


_limiter: LoginRateLimiter | None = None


def get_login_rate_limiter() -> LoginRateLimiter:
    global _limiter
    if _limiter is None:
        from app.config import get_settings

        settings = get_settings()
        _limiter = LoginRateLimiter(
            max_attempts=settings.login_rate_limit_attempts,
            window_minutes=settings.login_rate_limit_window_minutes,
        )
    return _limiter
