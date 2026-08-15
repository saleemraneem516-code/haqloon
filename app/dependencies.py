from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import ActivityLog, User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session) -> Optional[User]:
    """Look up the logged-in user from the signed session cookie.

    Returns None (never raises) so callers can decide how to redirect --
    keeps auth failures as ordinary control flow instead of exceptions.
    """
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return None
    return user


def log_activity(db: Session, request: Request, username: str, action: str) -> None:
    entry = ActivityLog(
        username=username,
        action=action,
        ip_address=request.client.host if request.client else None,
    )
    db.add(entry)
    db.commit()
