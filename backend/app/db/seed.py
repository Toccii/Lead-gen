"""Ensures the single dashboard user exists, from DASHBOARD_ADMIN_EMAIL / DASHBOARD_ADMIN_PASSWORD.
Idempotent: re-running (e.g. on every app startup) rotates the password hash to match the
current env vars, so changing the password is just an env var change + restart.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.user import User


def ensure_admin_user(db: Session) -> User:
    settings = get_settings()
    hashed = hash_password(settings.dashboard_admin_password)

    user = db.query(User).filter_by(email=settings.dashboard_admin_email).one_or_none()
    if user is None:
        user = User(email=settings.dashboard_admin_email, hashed_password=hashed)
        db.add(user)
    else:
        user.hashed_password = hashed

    db.commit()
    db.refresh(user)
    return user
