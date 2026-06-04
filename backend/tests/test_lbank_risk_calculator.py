"""Risk calculator tests."""
import pytest

from app.services.exchange.lbank_models import RiskLevel, Side
from app.services.widget import risk_calculator as rc


def test_long_distance():
    d = rc.liquidation_distance_percent(Side.long, mark_price=100, liquidation_price=90)
    assert d == pytest.approx(10.0)


def test_short_distance():
    d = rc.liquidation_distance_percent(Side.short, mark_price=100, liquidation_price=110)
    assert d == pytest.approx(10.0)


def test_distance_none_when_liq_missing():
    assert rc.liquidation_distance_percent(Side.long, 100, None) is None


def test_distance_none_when_mark_missing():
    assert rc.liquidation_distance_percent(Side.long, None, 90) is None


@pytest.mark.parametrize(
    "distance,expected",
    [
        (4.99, RiskLevel.high),
        (5.0, RiskLevel.medium),
        (9.99, RiskLevel.medium),
        (10.0, RiskLevel.safe),
        (50.0, RiskLevel.safe),
    ],
)
def test_classify_thresholds(distance, expected):
    assert rc.classify_risk(distance, mark_price=100, liquidation_price=90) == expected


def test_classify_unknown_when_liq_missing():
    assert rc.classify_risk(None, mark_price=100, liquidation_price=None) == RiskLevel.unknown


def test_classify_unknown_when_mark_missing():
    assert rc.classify_risk(None, mark_price=None, liquidation_price=90) == RiskLevel.unknown


def test_compute_position_risk_high():
    distance, level = rc.compute_position_risk(Side.long, mark_price=150, liquidation_price=146)
    assert level == RiskLevel.high
    assert distance == pytest.approx(2.6667, rel=1e-3)


def test_aggregate_prefers_most_severe_known():
    levels = [RiskLevel.safe, RiskLevel.medium, RiskLevel.unknown, RiskLevel.high]
    assert rc.aggregate_risk_level(levels) == RiskLevel.high


def test_aggregate_unknown_only_when_nothing_known():
    assert rc.aggregate_risk_level([RiskLevel.unknown]) == RiskLevel.unknown
    assert rc.aggregate_risk_level([]) == RiskLevel.unknown
