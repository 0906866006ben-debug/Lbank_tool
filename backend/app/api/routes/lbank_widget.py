"""LBank widget routes — strictly read-only + display-only settings.

No route here places, cancels, or modifies any real order, leverage,
margin mode, or balance. The TP/SL route stores DISPLAY prices only.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.database import get_session
from app.services.exchange.lbank_adapter import get_adapter
from app.services.exchange.lbank_models import (
    TestConnectionResponse,
    TpSlSettingsRequest,
    TpSlSettingsResponse,
    WidgetSummary,
)
from app.services.widget.lbank_widget_service import build_widget_summary

router = APIRouter(prefix="/api/lbank", tags=["lbank-widget"])

SNAPSHOT_ID = 1


def _load_pushed_summary(db: Session) -> WidgetSummary:
    from app.db.models.lbank_widget_snapshot import LbankWidgetSnapshot

    row = db.get(LbankWidgetSnapshot, SNAPSHOT_ID)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No pushed widget snapshot is available yet.",
        )
    return WidgetSummary.model_validate_json(row.payload_json)


def _save_pushed_summary(db: Session, payload: WidgetSummary) -> WidgetSummary:
    from app.db.models.lbank_widget_snapshot import LbankWidgetSnapshot

    clean_json = json.dumps(payload.model_dump(mode="json"), separators=(",", ":"))
    row = db.get(LbankWidgetSnapshot, SNAPSHOT_ID)
    if row is None:
        row = LbankWidgetSnapshot(
            id=SNAPSHOT_ID,
            payload_json=clean_json,
            received_at=datetime.now(timezone.utc),
        )
        db.add(row)
    else:
        row.payload_json = clean_json
        row.received_at = datetime.now(timezone.utc)
    db.commit()
    return payload


@router.get("/widget-summary", response_model=WidgetSummary)
def widget_summary(db: Session = Depends(get_session)) -> WidgetSummary:
    """Phone-sized widget payload. Read-only."""
    settings = get_settings()
    if settings.widget_source == "pushed":
        return _load_pushed_summary(db)
    return build_widget_summary(db=db)


@router.post("/widget-snapshot", response_model=WidgetSummary)
def push_widget_snapshot(
    payload: WidgetSummary,
    db: Session = Depends(get_session),
    x_sync_token: str | None = Header(default=None, alias="X-Sync-Token"),
) -> WidgetSummary:
    """Accept a sanitized widget snapshot from a trusted desktop syncer.

    This endpoint is only for display data. It never accepts or stores API
    credentials and it does not call LBank.
    """
    settings = get_settings()
    if not settings.sync_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Snapshot sync is not configured.",
        )
    if x_sync_token != settings.sync_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid sync token.",
        )
    return _save_pushed_summary(db, payload)


@router.post("/widget-settings/tpsl", response_model=TpSlSettingsResponse)
def set_tpsl_display(
    payload: TpSlSettingsRequest,
    db: Session = Depends(get_session),
) -> TpSlSettingsResponse:
    """Save DISPLAY-ONLY TP/SL prices. Never sent to LBank.

    Storing prices here does not place or modify any real TP/SL order and
    does not enable trading.
    """
    from app.db.models.lbank_widget_settings import LbankWidgetSettings

    row = db.get(LbankWidgetSettings, payload.position_key)
    if row is None:
        row = LbankWidgetSettings(position_key=payload.position_key)
        db.add(row)

    row.full_take_profit_price = payload.full_take_profit_price
    row.full_stop_loss_price = payload.full_stop_loss_price
    row.partial_take_profit_price = payload.partial_take_profit_price
    row.partial_stop_loss_price = payload.partial_stop_loss_price

    db.commit()

    return TpSlSettingsResponse(
        position_key=payload.position_key,
        full_take_profit_price=payload.full_take_profit_price,
        full_stop_loss_price=payload.full_stop_loss_price,
        partial_take_profit_price=payload.partial_take_profit_price,
        partial_stop_loss_price=payload.partial_stop_loss_price,
    )


@router.post("/test-connection", response_model=TestConnectionResponse)
def test_connection() -> TestConnectionResponse:
    """Read-only connectivity test. Never sends key/secret/sign in response,
    never calls a trading endpoint."""
    settings = get_settings()
    adapter = get_adapter(settings)
    try:
        ok, detail = adapter.test_connection()
    except NotImplementedError as exc:
        ok, detail = False, str(exc)
    return TestConnectionResponse(ok=ok, mock_mode=settings.mock_mode, detail=detail)
