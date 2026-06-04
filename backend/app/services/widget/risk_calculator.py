"""Risk metrics for the widget.

liquidation_distance_percent:
  - Long : abs(mark_price - liquidation_price) / mark_price * 100
  - Short: abs(liquidation_price - mark_price) / mark_price * 100
  (Both reduce to the same magnitude; side is kept explicit for clarity.)

risk_level thresholds (on liquidation_distance_percent):
  -        x < 5  -> high
  -  5 <=  x < 10 -> medium
  - 10 <=  x      -> safe
  - liquidation_price missing -> unknown
  - mark_price missing        -> unknown
"""
from __future__ import annotations

from typing import Optional

from app.services.exchange.lbank_models import RiskLevel, Side


def liquidation_distance_percent(
    side: Side,
    mark_price: Optional[float],
    liquidation_price: Optional[float],
) -> Optional[float]:
    if mark_price is None or liquidation_price is None:
        return None
    if mark_price == 0:
        return None
    if side == Side.long:
        return abs(mark_price - liquidation_price) / mark_price * 100
    return abs(liquidation_price - mark_price) / mark_price * 100


def classify_risk(
    distance_percent: Optional[float],
    *,
    mark_price: Optional[float],
    liquidation_price: Optional[float],
) -> RiskLevel:
    if mark_price is None or liquidation_price is None or distance_percent is None:
        return RiskLevel.unknown
    if distance_percent < 5:
        return RiskLevel.high
    if distance_percent < 10:
        return RiskLevel.medium
    return RiskLevel.safe


def compute_position_risk(
    side: Side,
    mark_price: Optional[float],
    liquidation_price: Optional[float],
) -> tuple[Optional[float], RiskLevel]:
    distance = liquidation_distance_percent(side, mark_price, liquidation_price)
    level = classify_risk(
        distance, mark_price=mark_price, liquidation_price=liquidation_price
    )
    return distance, level


# Account-level rollup: worst-case wins.
_SEVERITY = {
    RiskLevel.high: 3,
    RiskLevel.medium: 2,
    RiskLevel.safe: 1,
    RiskLevel.unknown: 0,
}


def aggregate_risk_level(levels: list[RiskLevel]) -> RiskLevel:
    if not levels:
        return RiskLevel.unknown
    # Prefer the most severe *known* level; only report unknown if nothing
    # else is known.
    known = [lvl for lvl in levels if lvl != RiskLevel.unknown]
    if not known:
        return RiskLevel.unknown
    return max(known, key=lambda lvl: _SEVERITY[lvl])
