"""Probe LBank contract API connectivity without printing secrets.

This script validates:
  - public contract API is reachable
  - local .env has an API key/secret
  - the official docs' read-only private example endpoint, prv/account,
    is reachable with the configured key/signature

It deliberately does not call any trading endpoint and never prints the
API key, secret, or signature.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import random
import string
import time
import urllib.parse
from pathlib import Path

import httpx


def _load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _get_json(url: str) -> tuple[int, str]:
    try:
        resp = httpx.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        return resp.status_code, resp.text[:300].replace("\n", " ")
    except httpx.HTTPError as exc:
        return 0, f"{type(exc).__name__}: {exc}"


def _rsa_sign(prepared: str, secret: str) -> str:
    try:
        from Crypto.Hash import SHA256
        from Crypto.PublicKey import RSA
        from Crypto.Signature import PKCS1_v1_5
    except ImportError as exc:
        raise RuntimeError(
            "RSA signing requires pycryptodome. Run: python -m pip install pycryptodome"
        ) from exc

    candidates = [secret] if "BEGIN" in secret else [
        "-----BEGIN PRIVATE KEY-----\n" + secret + "\n-----END PRIVATE KEY-----",
        "-----BEGIN RSA PRIVATE KEY-----\n" + secret + "\n-----END RSA PRIVATE KEY-----",
    ]
    last_error: Exception | None = None
    for pem in candidates:
        try:
            key = RSA.import_key(pem)
            digest = SHA256.new(prepared.encode("utf-8"))
            return base64.b64encode(PKCS1_v1_5.new(key).sign(digest)).decode("utf-8")
        except Exception as exc:  # Try the next common PEM wrapper.
            last_error = exc
    raise RuntimeError(f"Could not load RSA private key: {type(last_error).__name__}")


def _sign(params: dict[str, str], secret: str, signature_method: str) -> dict[str, str]:
    timestamp = str(int(time.time() * 1000))
    echostr = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(35))
    merged = dict(params)
    method = "RSA" if signature_method.upper() == "RSA" else "HmacSHA256"
    merged.update(
        {
            "timestamp": timestamp,
            "signature_method": method,
            "echostr": echostr,
        }
    )
    query = "&".join(f"{key}={value}" for key, value in sorted(merged.items()))
    prepared = hashlib.md5(query.encode("utf-8")).hexdigest().upper()
    if method == "RSA":
        merged["sign"] = _rsa_sign(prepared, secret)
    else:
        merged["sign"] = hmac.new(
            secret.encode("utf-8"),
            prepared.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    return merged


def _post_json(url: str, headers: dict[str, str], body: dict[str, str]) -> tuple[int, str]:
    try:
        resp = httpx.post(
            url,
            json=body,
            headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json", **headers},
            timeout=20,
        )
        return resp.status_code, resp.text[:300].replace("\n", " ")
    except httpx.HTTPError as exc:
        return 0, f"{type(exc).__name__}: {exc}"


def _post_form(url: str, headers: dict[str, str], body: dict[str, str]) -> tuple[int, str]:
    try:
        resp = httpx.post(
            url,
            content=urllib.parse.urlencode(body),
            headers={
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/x-www-form-urlencoded",
                **headers,
            },
            timeout=20,
        )
        return resp.status_code, resp.text[:300].replace("\n", " ")
    except httpx.HTTPError as exc:
        return 0, f"{type(exc).__name__}: {exc}"


def main() -> int:
    env = _load_env(Path(".env"))
    base_url = env.get("LBANK_BASE_URL", "https://lbkperp.lbank.com/").rstrip("/")
    api_key = env.get("LBANK_API_KEY", "")
    api_secret = env.get("LBANK_API_SECRET", "")
    signature_method = env.get("LBANK_SIGNATURE_METHOD", "HmacSHA256")

    print(f"api_key: {'set' if api_key else 'missing'} length={len(api_key)}")
    print(f"api_secret: {'set' if api_secret else 'missing'} length={len(api_secret)}")
    print(f"signature_method: {signature_method}")
    print(f"base_url: {base_url}")

    status, body = _get_json(f"{base_url}/cfd/openApi/v1/pub/getTime")
    print(f"public getTime: HTTP {status} {body[:120]}")

    if not api_key or not api_secret:
        print("private prv/account: skipped, missing key/secret")
        return 2

    spot_signed = _sign({"api_key": api_key}, api_secret, signature_method)
    spot_headers = {
        "timestamp": spot_signed["timestamp"],
        "signature_method": spot_signed["signature_method"],
        "echostr": spot_signed["echostr"],
    }
    spot_body = {"api_key": api_key, "sign": spot_signed["sign"]}
    status, text = _post_form(
        "https://api.lbkex.com/v2/supplement/api_Restrictions.do",
        spot_headers,
        spot_body,
    )
    print(f"spot api_Restrictions: HTTP {status} {text[:160]}")

    params = {
        "api_key": api_key,
        "asset": "USDT",
        "productGroup": "SwapU",
    }
    signed = _sign(params, api_secret, signature_method)
    headers = {
        "timestamp": signed["timestamp"],
        "signature_method": signed["signature_method"],
        "echostr": signed["echostr"],
    }
    body = {
        "api_key": signed["api_key"],
        "asset": signed["asset"],
        "productGroup": signed["productGroup"],
        "sign": signed["sign"],
    }
    status, text = _post_json(
        f"{base_url}/cfd/openApi/v1/prv/account",
        headers,
        body,
    )
    print(f"contract prv/account json: HTTP {status} {text[:160]}")
    status, text = _post_form(
        f"{base_url}/cfd/openApi/v1/prv/account",
        headers,
        body,
    )
    print(f"contract prv/account form: HTTP {status} {text[:160]}")
    return 0 if status == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
