"""Pydantic models for the LBank Futures Position Widget (read-only).

These models describe what the widget *displays*. None of them carry any
trading instruction. Partial TP/SL fields intentionally expose only a
*price* — never a quantity — per the product rules.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field


class Side(str, Enum):
    long = "long"
    short = "short"


class PositionMode(str, Enum):
    one_way = "one_way"
    hedge = "hedge"


class MarginMode(str, Enum):
    isolated = "isolated"
    cross = "cross"


class RiskLevel(str, Enum):
    safe = "safe"
    medium = "medium"
    high = "high"
    unknown = "unknown"


class Position(BaseModel):
    """A single open position as shown in the widget.

    `position_key` = account_id + symbol + side + margin_mode + position_mode.
    In Hedge Mode a single `symbol` can hold both long and short at once, so
    `symbol` alone is NOT a unique key.
    """

    symbol: str
    side: Side
    position_mode: PositionMode
    margin_mode: MarginMode
    leverage: Optional[int] = None

    unrealized_pnl: Optional[float] = None
    roe_percent: Optional[float] = None

    mark_price: Optional[float] = None
    last_price: Optional[float] = None
    entry_price: Optional[float] = None
    liquidation_price: Optional[float] = None

    # Display-only TP/SL prices. Full = whole position, partial = fixed amount.
    # Widget shows the PRICE only, never the quantity.
    full_take_profit_price: Optional[float] = None
    full_stop_loss_price: Optional[float] = None
    partial_take_profit_price: Optional[float] = None
    partial_stop_loss_price: Optional[float] = None

    # Notional used purely for widget ordering (high notional ranks higher).
    notional: Optional[float] = Field(default=None, exclude=True)

    # Computed/derived fields, filled by the risk calculator. Kept optional so
    # the adapter can leave them unset and the service fills them in.
    liquidation_distance_percent: Optional[float] = None
    risk_level: RiskLevel = RiskLevel.unknown

    # account_id is part of the key but never surfaced raw if sensitive; here
    # it is a non-secret logical account label.
    account_id: str = Field(default="default", exclude=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def position_key(self) -> str:
        return f"{self.symbol}:{self.side.value}:{self.margin_mode.value}:{self.position_mode.value}"


class WidgetSummary(BaseModel):
    exchange: str = "LBank"
    account_type: str = "futures"
    updated_at: str
    total_unrealized_pnl: Optional[float] = None
    total_roe_percent: Optional[float] = None
    risk_level: RiskLevel = RiskLevel.unknown
    positions: List[Position] = Field(default_factory=list)
    # Number of positions beyond what the widget shows -> render "+N more".
    more_count: int = 0


class TpSlSettingsRequest(BaseModel):
    """Display-only TP/SL prices. NOTHING here is sent to LBank."""

    position_key: str
    full_take_profit_price: Optional[float] = None
    full_stop_loss_price: Optional[float] = None
    partial_take_profit_price: Optional[float] = None
    partial_stop_loss_price: Optional[float] = None


class TpSlSettingsResponse(BaseModel):
    position_key: str
    full_take_profit_price: Optional[float] = None
    full_stop_loss_price: Optional[float] = None
    partial_take_profit_price: Optional[float] = None
    partial_stop_loss_price: Optional[float] = None
    saved: bool = True
    note: str = "Display-only. Not sent to LBank; does not change real TP/SL."


class TestConnectionResponse(BaseModel):
    ok: bool
    mock_mode: bool
    # Read-only test result only. Never includes key/secret/sign.
    detail: str
