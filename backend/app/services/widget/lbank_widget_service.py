"""Builds the widget summary — flat, ready-to-render data for an Android
(Jetpack Glance) widget to consume directly, with no client-side math.

Responsibilities:
  - Pull positions from the adapter (mock or real).
  - Overlay display-only TP/SL prices saved by the user.
  - Compute risk metrics.
  - Order and trim positions for the small widget surface.
  - Roll up account-level totals.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from app.services.exchange.lbank_adapter import LBankAdapter, get_adapter
from app.services.exchange.lbank_models import Position, RiskLevel, WidgetSummary
from app.services.widget import risk_calculator

MAX_WIDGET_POSITIONS = 3

# Ordering severity: high risk first, then losing PnL, then nearest
# liquidation, then larger notional.
_RISK_ORDER = {
    RiskLevel.high: 0,
    RiskLevel.medium: 1,
    RiskLevel.unknown: 2,
    RiskLevel.safe: 3,
}


def _apply_saved_tpsl(positions: List[Position], db: Optional[Session]) -> None:
    if db is None:
        return
    from app.db.models.lbank_widget_settings import LbankWidgetSettings

    keys = [p.position_key for p in positions]
    rows = (
        db.query(LbankWidgetSettings)
        .filter(LbankWidgetSettings.position_key.in_(keys))
        .all()
    )
    by_key = {r.position_key: r for r in rows}
    for p in positions:
        row = by_key.get(p.position_key)
        if row is None:
            continue
        # Saved display settings override adapter-provided display prices.
        if row.full_take_profit_price is not None:
            p.full_take_profit_price = row.full_take_profit_price
        if row.full_stop_loss_price is not None:
            p.full_stop_loss_price = row.full_stop_loss_price
        if row.partial_take_profit_price is not None:
            p.partial_take_profit_price = row.partial_take_profit_price
        if row.partial_stop_loss_price is not None:
            p.partial_stop_loss_price = row.partial_stop_loss_price


def _enrich_risk(positions: Iterable[Position]) -> None:
    for p in positions:
        distance, level = risk_calculator.compute_position_risk(
            p.side, p.mark_price, p.liquidation_price
        )
        p.liquidation_distance_percent = distance
        p.risk_level = level


def _sort_key(p: Position):
    risk_rank = _RISK_ORDER.get(p.risk_level, 2)
    pnl = p.unrealized_pnl if p.unrealized_pnl is not None else 0.0
    # nearest liquidation first => smaller distance ranks earlier
    distance = (
        p.liquidation_distance_percent
        if p.liquidation_distance_percent is not None
        else float("inf")
    )
    notional = p.notional if p.notional is not None else 0.0
    return (risk_rank, pnl, distance, -notional)


def order_and_trim(positions: List[Position]) -> tuple[List[Position], int]:
    ordered = sorted(positions, key=_sort_key)
    shown = ordered[:MAX_WIDGET_POSITIONS]
    more = max(0, len(ordered) - MAX_WIDGET_POSITIONS)
    return shown, more


def build_widget_summary(
    db: Optional[Session] = None,
    adapter: Optional[LBankAdapter] = None,
) -> WidgetSummary:
    adapter = adapter or get_adapter()
    positions = adapter.get_positions()

    _apply_saved_tpsl(positions, db)
    _enrich_risk(positions)
    shown, more = order_and_trim(positions)

    total_pnl = sum(
        (p.unrealized_pnl or 0.0) for p in positions if p.unrealized_pnl is not None
    )
    roes = [p.roe_percent for p in positions if p.roe_percent is not None]
    total_roe = round(sum(roes) / len(roes), 4) if roes else None

    account_risk = risk_calculator.aggregate_risk_level([p.risk_level for p in positions])

    return WidgetSummary(
        updated_at=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        total_unrealized_pnl=round(total_pnl, 8) if positions else None,
        total_roe_percent=total_roe,
        risk_level=account_risk,
        positions=shown,
        more_count=more,
    )
