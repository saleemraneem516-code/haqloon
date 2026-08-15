"""
Security primitives: bcrypt password hashing + per-session CSRF tokens.
"""
import secrets

from fastapi import Request
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(plain_password, password_hash)
    except Exception:
        return False


def get_csrf_token(request: Request) -> str:
    """Return the CSRF token for this session, creating one if absent."""
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_hex(32)
        request.session["csrf_token"] = token
    return token


def verify_csrf(request: Request, submitted_token: str) -> bool:
    expected = request.session.get("csrf_token")
    return bool(expected) and secrets.compare_digest(expected, submitted_token or "")
