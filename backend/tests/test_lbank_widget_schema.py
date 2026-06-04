"""Widget schema / service behaviour tests."""
from app.services.exchange.lbank_models import (
    MarginMode,
    Position,
    PositionMode,
    RiskLevel,
    Side,
)
from app.services.widget import lbank_widget_service as svc


def _mk(symbol, side, mark, liq, pnl=0.0, mode=PositionMode.one_way):
    return Position(
        symbol=symbol,
        side=side,
        position_mode=mode,
        margin_mode=MarginMode.isolated,
        mark_price=mark,
        liquidation_price=liq,
        unrealized_pnl=pnl,
    )


def test_position_key_is_composite_not_just_symbol():
    p = _mk("BTCUSDT", Side.long, 100, 90)
    assert p.position_key == "BTCUSDT:long:isolated:one_way"
    assert p.position_key != "BTCUSDT"


def test_hedge_mode_long_short_same_symbol_distinct_keys():
    long_p = Position(
        symbol="BTCUSDT", side=Side.long, position_mode=PositionMode.hedge,
        margin_mode=MarginMode.isolated,
    )
    short_p = Position(
        symbol="BTCUSDT", side=Side.short, position_mode=PositionMode.hedge,
        margin_mode=MarginMode.isolated,
    )
    assert long_p.position_key != short_p.position_key


def test_summary_trims_to_max_three_and_reports_more():
    positions = [
        _mk("A", Side.long, 100, 99, pnl=-5),   # high risk
        _mk("B", Side.long, 100, 90, pnl=-1),   # safe
        _mk("C", Side.long, 100, 90, pnl=2),    # safe
        _mk("D", Side.long, 100, 90, pnl=3),    # safe
        _mk("E", Side.long, 100, 90, pnl=4),    # safe
    ]

    class FakeAdapter:
        def get_positions(self):
            return positions

        def test_connection(self):
            return True, "ok"

    summary = svc.build_widget_summary(db=None, adapter=FakeAdapter())
    assert len(summary.positions) == 3
    assert summary.more_count == 2
    # High risk must be ranked first.
    assert summary.positions[0].symbol == "A"
    assert summary.positions[0].risk_level == RiskLevel.high


def test_missing_liquidation_yields_unknown_risk():
    class FakeAdapter:
        def get_positions(self):
            return [_mk("XRPUSDT", Side.short, 0.52, None)]

        def test_connection(self):
            return True, "ok"

    summary = svc.build_widget_summary(db=None, adapter=FakeAdapter())
    assert summary.positions[0].risk_level == RiskLevel.unknown
    assert summary.positions[0].liquidation_distance_percent is None


def test_missing_tpsl_serializes_as_null():
    p = _mk("BTCUSDT", Side.long, 100, 90)
    dumped = p.model_dump()
    assert dumped["full_take_profit_price"] is None
    assert dumped["partial_take_profit_price"] is None


def test_partial_tpsl_has_no_quantity_field():
    """Partial TP/SL must expose price only — never a quantity."""
    fields = Position.model_fields.keys()
    for f in fields:
        assert "quantity" not in f
        assert "amount" not in f or f.endswith("price") is False
    # explicit: partial fields are price-only
    assert "partial_take_profit_price" in fields
    assert "partial_take_profit_quantity" not in fields
    assert "partial_stop_loss_quantity" not in fields
