"""Exchange adapter abstraction.

The widget reads positions through an abstract adapter so the first-version
main line can run entirely on mock data. The real adapter is intentionally
NOT functional: LBank's public docs cover Spot only and do not document
Futures position / TP-SL query endpoints, so we must not guess real paths,
params, or response shapes.

READ-ONLY: the interface exposes only queries. There is deliberately no
place_order / cancel / set_leverage / set_tpsl / withdraw method anywhere.
"""
from __future__ import annotations

import abc
from typing import List, Optional

from app.config import Settings, get_settings
from app.services.exchange.lbank_models import (
    MarginMode,
    Position,
    PositionMode,
    Side,
)


class LBankAdapter(abc.ABC):
    """Read-only position source."""

    @abc.abstractmethod
    def get_positions(self) -> List[Position]:
        """Return open positions. Read-only."""

    @abc.abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Read-only connectivity check. Returns (ok, detail).

        MUST NOT include api_key / api_secret / sign in the detail string.
        """


class MockLBankAdapter(LBankAdapter):
    """First-version main line. Realistic shapes, but NO real keys/secret/sign.

    Mock set covers, per spec:
      - BTCUSDT Long
      - ETHUSDT Short
      - one position missing liquidation_price (risk -> unknown)
      - one high-risk position
      - one position with no TP/SL configured
    """

    def get_positions(self) -> List[Position]:
        return [
            # BTCUSDT Long — safe, full + partial TP/SL set
            Position(
                symbol="BTCUSDT",
                side=Side.long,
                position_mode=PositionMode.hedge,
                margin_mode=MarginMode.isolated,
                leverage=20,
                unrealized_pnl=18.5,
                roe_percent=12.3,
                mark_price=69100,
                last_price=69120,
                entry_price=68200,
                liquidation_price=64800,
                full_take_profit_price=71000,
                full_stop_loss_price=67000,
                partial_take_profit_price=70500,
                partial_stop_loss_price=67500,
                notional=69100 * 0.5,
            ),
            # ETHUSDT Short — losing position, full TP/SL set
            Position(
                symbol="ETHUSDT",
                side=Side.short,
                position_mode=PositionMode.hedge,
                margin_mode=MarginMode.isolated,
                leverage=10,
                unrealized_pnl=-6.2,
                roe_percent=-3.1,
                mark_price=3720,
                last_price=3722,
                entry_price=3690,
                liquidation_price=3980,
                full_take_profit_price=3600,
                full_stop_loss_price=3760,
                partial_take_profit_price=3630,
                partial_stop_loss_price=3740,
                notional=3720 * 2,
            ),
            # SOLUSDT Long — HIGH risk (close to liquidation), no TP/SL set
            Position(
                symbol="SOLUSDT",
                side=Side.long,
                position_mode=PositionMode.one_way,
                margin_mode=MarginMode.cross,
                leverage=50,
                unrealized_pnl=-12.0,
                roe_percent=-40.0,
                mark_price=150.0,
                last_price=149.8,
                entry_price=156.0,
                liquidation_price=146.0,  # ~2.7% away -> high
                full_take_profit_price=None,
                full_stop_loss_price=None,
                partial_take_profit_price=None,
                partial_stop_loss_price=None,
                notional=150 * 10,
            ),
            # XRPUSDT Short — liquidation_price MISSING -> risk unknown
            Position(
                symbol="XRPUSDT",
                side=Side.short,
                position_mode=PositionMode.one_way,
                margin_mode=MarginMode.cross,
                leverage=5,
                unrealized_pnl=2.1,
                roe_percent=1.4,
                mark_price=0.52,
                last_price=0.521,
                entry_price=0.53,
                liquidation_price=None,
                full_take_profit_price=0.50,
                full_stop_loss_price=0.55,
                partial_take_profit_price=None,
                partial_stop_loss_price=None,
                notional=0.52 * 1000,
            ),
        ]

    def test_connection(self) -> tuple[bool, str]:
        return True, "Mock mode: no real API call performed."


class RealLBankAdapter(LBankAdapter):
    """Real read-only adapter — NOT functional yet.

    Every method raises until the endpoints are verified against LBank's
    docs / real testing. We refuse to guess request paths or response
    schemas. Signing (HmacSHA256) is implemented in lbank_signer and can be
    wired here once the read-only Futures position-query endpoint is
    confirmed.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()

    def get_positions(self) -> List[Position]:
        # TODO(unverified-endpoint): LBank's public docs (Spot V2) do not
        # document a Futures/perpetual position-query REST path or its
        # response schema. Do NOT hardcode a guessed path. Once a read-only
        # endpoint is confirmed:
        #   1. Build read-only query params.
        #   2. sign_request(params, secret) via lbank_signer (HmacSHA256).
        #   3. POST x-www-form-urlencoded to the verified endpoint.
        #   4. Map the verified response -> List[Position].
        # This must remain read-only: never place/cancel/modify orders.
        raise NotImplementedError(
            "RealLBankAdapter.get_positions: LBank Futures position endpoint "
            "is not verified. Keep LBANK_WIDGET_MOCK_MODE=true until confirmed."
        )

    def test_connection(self) -> tuple[bool, str]:
        # TODO(unverified-endpoint): use a confirmed read-only endpoint
        # (e.g. account-readable query) to validate the key. Never call a
        # trading endpoint to "test". Never echo key/secret/sign.
        raise NotImplementedError(
            "RealLBankAdapter.test_connection: no verified read-only endpoint."
        )


def get_adapter(settings: Optional[Settings] = None) -> LBankAdapter:
    settings = settings or get_settings()
    if settings.mock_mode:
        return MockLBankAdapter()
    return RealLBankAdapter(settings)
