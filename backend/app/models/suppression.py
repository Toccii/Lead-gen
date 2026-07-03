from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Suppression(TimestampMixin, Base):
    """Global do-not-contact list. Checked by the sourcing module before any lead is created,
    so an opted-out (or manually erased) email can never re-enter any campaign, present or future.
    """

    __tablename__ = "suppressions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "opt_out_link", "manual"
