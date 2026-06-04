"""Signer tests — HmacSHA256 flow per the official Spot docs."""
import hashlib
import hmac

import pytest

from app.services.exchange import lbank_signer as s


def test_build_sign_params_excludes_existing_sign_and_injects_required():
    params = {"symbol": "btc_usdt", "sign": "SHOULD_BE_DROPPED"}
    out = s.build_sign_params(
        params, timestamp="1700000000000", echostr="abc", signature_method="HmacSHA256"
    )
    assert "sign" not in out
    assert out["signature_method"] == "HmacSHA256"
    assert out["timestamp"] == "1700000000000"
    assert out["echostr"] == "abc"
    assert out["symbol"] == "btc_usdt"


def test_prepared_str_is_sorted_md5_uppercase():
    sign_params = {"b": "2", "a": "1", "c": "3"}
    prepared = s.build_prepared_str(sign_params)
    # Recompute expected: sorted -> a=1&b=2&c=3 -> md5 hex -> upper
    expected = hashlib.md5(b"a=1&b=2&c=3").hexdigest().upper()
    assert prepared == expected
    assert prepared == prepared.upper()


def test_hmac_sha256_matches_reference():
    prepared = "ABCDEF1234567890"
    secret = "my_secret"
    expected = hmac.new(
        secret.encode(), prepared.encode(), hashlib.sha256
    ).hexdigest()
    assert s.hmac_sha256_sign(prepared, secret) == expected


def test_sign_request_includes_sign_and_required_params():
    out = s.sign_request(
        {"symbol": "btc_usdt"},
        secret_key="secret",
        timestamp="1700000000000",
        echostr="echo123",
    )
    assert "sign" in out
    assert out["signature_method"] == "HmacSHA256"
    assert out["timestamp"] == "1700000000000"
    assert out["echostr"] == "echo123"


def test_sign_value_never_appears_in_signed_string():
    """`sign` must not be part of the string that is signed."""
    params = {"symbol": "btc_usdt"}
    ts, es = "1700000000000", "echo123"
    out = s.sign_request(params, secret_key="secret", timestamp=ts, echostr=es)

    # Reconstruct what was signed and ensure 'sign' key is absent from it.
    sign_params = s.build_sign_params(
        params, timestamp=ts, echostr=es, signature_method="HmacSHA256"
    )
    assert "sign" not in sign_params
    prepared = s.build_prepared_str(sign_params)
    # The produced sign must equal HMAC over preparedStr (which had no sign).
    assert out["sign"] == s.hmac_sha256_sign(prepared, "secret")


def test_sign_request_does_not_mutate_input():
    params = {"symbol": "btc_usdt"}
    s.sign_request(params, secret_key="secret", timestamp="1", echostr="echo1234567890")
    assert params == {"symbol": "btc_usdt"}


def test_echostr_length_bounds():
    assert 30 <= len(s.generate_echostr()) <= 40
    with pytest.raises(ValueError):
        s.generate_echostr(10)


def test_non_hmac_method_not_implemented():
    with pytest.raises(NotImplementedError):
        s.sign_request({"a": 1}, secret_key="x", signature_method="RSA")
