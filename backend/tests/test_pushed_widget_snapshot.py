from app.config import get_settings
from app.main import create_app
from fastapi.testclient import TestClient
import pytest


@pytest.fixture(autouse=True)
def clear_settings_cache():
    yield
    get_settings.cache_clear()


def _summary_payload(symbol="BTCUSDT"):
    return {
        "exchange": "LBank",
        "account_type": "futures",
        "updated_at": "2026-06-05T00:00:00+08:00",
        "total_unrealized_pnl": 1.23,
        "total_roe_percent": 4.56,
        "risk_level": "safe",
        "positions": [
            {
                "symbol": symbol,
                "side": "long",
                "position_mode": "hedge",
                "margin_mode": "isolated",
                "leverage": 10,
                "unrealized_pnl": 1.23,
                "roe_percent": 4.56,
                "mark_price": 100.0,
                "entry_price": 95.0,
                "liquidation_price": 80.0,
                "risk_level": "safe",
            }
        ],
        "more_count": 0,
    }


def _client(monkeypatch, *, source="adapter", token="sync-token"):
    monkeypatch.setenv("LBANK_WIDGET_SOURCE", source)
    monkeypatch.setenv("LBANK_SYNC_TOKEN", token)
    get_settings.cache_clear()
    return TestClient(create_app())


def test_snapshot_push_requires_configured_token(monkeypatch):
    client = _client(monkeypatch, token="")
    resp = client.post("/api/lbank/widget-snapshot", json=_summary_payload())
    assert resp.status_code == 403


def test_snapshot_push_rejects_wrong_token(monkeypatch):
    client = _client(monkeypatch, token="good-token")
    resp = client.post(
        "/api/lbank/widget-snapshot",
        json=_summary_payload(),
        headers={"X-Sync-Token": "bad-token"},
    )
    assert resp.status_code == 401


def test_pushed_source_returns_latest_snapshot(monkeypatch):
    client = _client(monkeypatch, source="pushed", token="good-token")
    pushed = client.post(
        "/api/lbank/widget-snapshot",
        json=_summary_payload("ETHUSDT"),
        headers={"X-Sync-Token": "good-token"},
    )
    assert pushed.status_code == 200

    resp = client.get("/api/lbank/widget-summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["positions"][0]["symbol"] == "ETHUSDT"
    assert "api_key" not in str(body).lower()
    assert "api_secret" not in str(body).lower()
