"""David Wallace's approver login.

* The password is never stored. hw5/.env holds only APPROVER_PASSWORD_HASH, a
  salted PBKDF2-SHA256 hash written by set_approver_password.py.
* Passwords are checked with a constant-time comparison.
* Sessions are random tokens that expire after SESSION_MINUTES.
* After MAX_FAILED_LOGINS wrong guesses, login is locked for LOCKOUT_MINUTES.

Classroom-level protection: a real business would add single sign-on and
two-factor login for anyone who can approve money.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time

from dotenv import dotenv_values

from config import HUMAN_APPROVER, ROOT

HASH_ENV = "APPROVER_PASSWORD_HASH"
ITERATIONS = 600_000
SESSION_MINUTES = 30
MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 5

_sessions: dict[str, float] = {}          # token -> expiry time
_failures: dict[str, list[float]] = {}    # client -> times of recent failed logins


def hash_password(password: str, iterations: int = ITERATIONS) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    b64 = lambda b: base64.b64encode(b).decode("ascii")  # noqa: E731
    return f"pbkdf2_sha256${iterations}${b64(salt)}${b64(digest)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt, digest = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        expected = base64.b64decode(digest)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), base64.b64decode(salt), int(iterations)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def stored_hash() -> str | None:
    """Read the hash fresh each time, so setting a password needs no restart."""
    value = os.environ.get(HASH_ENV) or dotenv_values(ROOT / ".env").get(HASH_ENV)
    return value.strip() if value and value.strip() else None


class LoginError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status, self.message = status, message


def login(password: str, client: str) -> dict:
    now = time.time()
    recent = [t for t in _failures.get(client, []) if now - t < LOCKOUT_MINUTES * 60]
    _failures[client] = recent
    if len(recent) >= MAX_FAILED_LOGINS:
        wait = int(LOCKOUT_MINUTES * 60 - (now - recent[0])) + 1
        raise LoginError(429, f"Too many wrong passwords. Login is locked for {wait} more seconds.")
    stored = stored_hash()
    if stored is None:
        raise LoginError(503, "No approver password is set. Run backend/set_approver_password.py first.")
    if not verify_password(password, stored):
        recent.append(now)
        left = MAX_FAILED_LOGINS - len(recent)
        raise LoginError(401, f"Wrong password. {left} {'try' if left == 1 else 'tries'} left before a {LOCKOUT_MINUTES}-minute lockout.")
    _failures.pop(client, None)
    token = secrets.token_urlsafe(32)
    _sessions[token] = now + SESSION_MINUTES * 60
    return {"token": token, "approver": HUMAN_APPROVER, "expires_in_minutes": SESSION_MINUTES}


def logout(token: str | None) -> None:
    if token:
        _sessions.pop(token, None)


def check_session(token: str | None) -> str:
    """Return the approver's name for a valid session, or raise LoginError."""
    if stored_hash() is None:
        raise LoginError(503, "No approver password is set. Run backend/set_approver_password.py first.")
    expiry = _sessions.get(token or "")
    if expiry is None:
        raise LoginError(401, f"Only {HUMAN_APPROVER} can do this. Please log in.")
    if expiry < time.time():
        _sessions.pop(token, None)
        raise LoginError(401, "Your session expired. Please log in again.")
    return HUMAN_APPROVER
