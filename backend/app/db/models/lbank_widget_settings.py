"""Display-only TP/SL settings, keyed by position_key.

Stores PRICES only. There is no quantity column for partial TP/SL, by
design — the widget never shows partial amounts, and we never send these
to LBank.
"""
from __future__ import annotations

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class LbankWidgetSettings(Base):
    __tablename__ = "lbank_widget_settings"

    position_key: Mapped[str] = mapped_column(String, primary_key=True)
    full_take_profit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    full_stop_loss_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    partial_take_profit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    partial_stop_loss_price: Mapped[float | None] = mapped_column(Float, nullable=True)
