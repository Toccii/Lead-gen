"""Password hashing and JWT helpers for the single-user dashboard login (built out in Phase 5),
plus HMAC-signed unsubscribe tokens used in the email compliance footer (Phase 3).
"""
from __future__ import annotations

import hashlib
import hmac

from app.core.config import get_settings


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
