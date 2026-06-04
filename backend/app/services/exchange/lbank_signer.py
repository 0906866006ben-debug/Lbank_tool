"""LBank HmacSHA256 request signing, per the official Spot API docs.

This is the one signing flow LBank publishes openly, so it is safe to
implement and test. RSA is out of scope for the first version.

Flow (from the public docs):
  1. Collect all parameters to be signed, EXCLUDING `sign`. Add
     `signature_method`, `timestamp` (ms), and `echostr` to that set.
  2. Sort parameters by key name (ASCII order).
  3. Join into a query string: k1=v1&k2=v2...
  4. MD5 the query string (hex) and UPPERCASE it -> preparedStr.
  5. HMAC-SHA256(preparedStr) with the secret key (hex output) -> sign.
  6. Send `sign` alongside the other params.

IMPORTANT: `sign` itself must NEVER be part of the string being signed.

Read-only scope: this module only *signs* requests. It has no notion of
order/withdrawal endpoints. Higher layers must only ever sign read-only
queries.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import string
import time
from typing import Dict, Mapping

_ECHOSTR_ALPHABET = string.ascii_letters + string.digits


def now_timestamp_ms() -> str:
    """Millisecond timestamp as a string. In production, prefer LBank's
    server-time endpoint to avoid clock skew (see RealLBankAdapter TODO)."""
    return str(int(time.time() * 1000))


def generate_echostr(length: int = 35) -> str:
    """Random alphanumeric string, 30-40 chars per the docs."""
    if not 30 <= length <= 40:
        raise ValueError("echostr length must be between 30 and 40")
    return "".join(secrets.choice(_ECHOSTR_ALPHABET) for _ in range(length))


def build_sign_params(
    params: Mapping[str, object],
    *,
    timestamp: str,
    echostr: str,
    signature_method: str = "HmacSHA256",
) -> Dict[str, str]:
    """Return the parameter set used for signing.

    Drops any pre-existing `sign`, then injects the three required signing
    parameters. Values are stringified.
    """
    merged: Dict[str, str] = {
        k: str(v) for k, v in params.items() if k != "sign" and v is not None
    }
    merged["signature_method"] = signature_method
    merged["timestamp"] = timestamp
    merged["echostr"] = echostr
    return merged


def build_prepared_str(sign_params: Mapping[str, str]) -> str:
    """Sort by key, join as query string, MD5(hex) and uppercase."""
    ordered = sorted(sign_params.items(), key=lambda kv: kv[0])
    query_string = "&".join(f"{k}={v}" for k, v in ordered)
    md5_hex = hashlib.md5(query_string.encode("utf-8")).hexdigest()
    return md5_hex.upper()


def hmac_sha256_sign(prepared_str: str, secret_key: str) -> str:
    """HMAC-SHA256 of preparedStr using the secret, hex output."""
    return hmac.new(
        secret_key.encode("utf-8"),
        prepared_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def sign_request(
    params: Mapping[str, object],
    secret_key: str,
    *,
    timestamp: str | None = None,
    echostr: str | None = None,
    signature_method: str = "HmacSHA256",
) -> Dict[str, str]:
    """Produce the full outgoing parameter dict including `sign`.

    Returns a new dict; never mutates the input. The returned dict is the
    body to send as application/x-www-form-urlencoded.
    """
    if signature_method != "HmacSHA256":
        raise NotImplementedError(
            f"Only HmacSHA256 is implemented; got {signature_method!r}"
        )

    ts = timestamp or now_timestamp_ms()
    es = echostr or generate_echostr()

    sign_params = build_sign_params(
        params, timestamp=ts, echostr=es, signature_method=signature_method
    )
    prepared = build_prepared_str(sign_params)
    sign = hmac_sha256_sign(prepared, secret_key)

    outgoing = dict(sign_params)
    outgoing["sign"] = sign
    return outgoing
