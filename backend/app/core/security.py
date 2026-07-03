"""Password hashing and JWT helpers for the single-user dashboard login (Phase 5), plus
HMAC-signed unsubscribe tokens used in the email compliance footer (Phase 3).
"""
from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(password, hashed_password)


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    return payload.get("sub")


def _sign(lead_id: int) -> str:
    settings = get_settings()
    return hmac.new(settings.secret_key.encode(), str(lead_id).encode(), hashlib.sha256).hexdigest()


def build_unsubscribe_token(lead_id: int) -> str:
    return f"{lead_id}.{_sign(lead_id)}"


def verify_unsubscribe_token(token: str) -> int | None:
    try:
        lead_id_str, signature = token.split(".", 1)
        lead_id = int(lead_id_str)
    except (ValueError, AttributeError):
        return None
    if not hmac.compare_digest(_sign(lead_id), signature):
        return None
    return lead_id


def build_unsubscribe_url(lead_id: int) -> str:
    settings = get_settings()
    token = build_unsubscribe_token(lead_id)
    return f"{settings.unsubscribe_base_url.rstrip('/')}/{token}"
