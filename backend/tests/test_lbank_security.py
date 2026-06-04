"""Security tests: secrets/keys/sign must never leak outward."""
import json

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.exchange.lbank_adapter import MockLBankAdapter

FORBIDDEN_SUBSTRINGS = ["secret", "sign", "api_key", "apisecret"]


def _assert_clean(blob: str):
    low = blob.lower()
    for needle in FORBIDDEN_SUBSTRINGS:
        assert needle not in low, f"leaked {needle!r} in: {blob[:200]}"


def test_widget_summary_has_no_secret_or_sign():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/lbank/widget-summary")
    assert resp.status_code == 200
    _assert_clean(json.dumps(resp.json()))


def test_test_connection_has_no_secret_or_sign():
    app = create_app()
    client = TestClient(app)
    resp = client.post("/api/lbank/test-connection")
    assert resp.status_code == 200
    body = resp.json()
    assert body["mock_mode"] is True
    _assert_clean(json.dumps(body))


def test_healthz_does_not_expose_key_or_secret():
    app = create_app()
    client = TestClient(app)
    body = client.get("/healthz").json()
    # base_url / mock_mode / signature_method are fine; key/secret are not.
    assert "api_key" not in body
    assert "api_secret" not in json.dumps(body).lower()


def test_mock_adapter_positions_contain_no_credentials():
    positions = MockLBankAdapter().get_positions()
    for p in positions:
        dumped = json.dumps(p.model_dump())
        assert "secret" not in dumped.lower()
        assert "api_key" not in dumped.lower()
        assert "sign" not in dumped.lower()


def test_credential_public_dict_omits_secret():
    from app.db.models.lbank_api_credentials import LbankApiCredential

    cred = LbankApiCredential(
        account_id="acct1", api_key="KEY", api_secret="SUPERSECRET", read_only=True
    )
    public = cred.to_public_dict()
    assert "api_secret" not in public
    assert "api_key" not in public
    assert "SUPERSECRET" not in json.dumps(public)
    assert public["read_only"] is True


def test_tpsl_settings_never_claims_to_send_to_lbank():
    app = create_app()
    client = TestClient(app)
    resp = client.post(
        "/api/lbank/widget-settings/tpsl",
        json={
            "position_key": "BTCUSDT:long:isolated:hedge",
            "full_take_profit_price": 71000,
            "full_stop_loss_price": 67000,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["saved"] is True
    assert "not sent to lbank" in body["note"].lower()
