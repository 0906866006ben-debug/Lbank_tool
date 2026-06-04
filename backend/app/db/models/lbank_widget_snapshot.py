"""Latest sanitized widget snapshot pushed by a trusted desktop syncer.

This table stores display data only. It never stores LBank credentials,
request signatures, or raw exchange responses.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class LbankWidgetSnapshot(Base):
    __tablename__ = "lbank_widget_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
