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

import hashlib
import hmac
import json
import os
import random
import string
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


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


def _safe_read_error(exc: urllib.error.HTTPError) -> str:
    body = exc.read().decode("utf-8", errors="replace")
    return body[:300].replace("\n", " ")


def _get_json(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")[:300]
    except urllib.error.HTTPError as exc:
        return exc.code, _safe_read_error(exc)


def _sign(params: dict[str, str], secret: str, signature_method: str) -> dict[str, str]:
    timestamp = str(int(time.time() * 1000))
    echostr = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(35))
    merged = dict(params)
    merged.update(
        {
            "timestamp": timestamp,
            "signature_method": signature_method,
            "echostr": echostr,
        }
    )
    query = "&".join(f"{key}={value}" for key, value in sorted(merged.items()))
    prepared = hashlib.md5(query.encode("utf-8")).hexdigest().upper()
    merged["sign"] = hmac.new(
        secret.encode("utf-8"),
        prepared.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return merged


def _post_json(url: str, headers: dict[str, str], body: dict[str, str]) -> tuple[int, str]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json", **headers},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")[:300]
    except urllib.error.HTTPError as exc:
        return exc.code, _safe_read_error(exc)


def main() -> int:
    env = _load_env(Path(".env"))
    base_url = env.get("LBANK_BASE_URL", "https://lbkperp.lbank.com/").rstrip("/")
    api_key = env.get("LBANK_API_KEY", "")
    api_secret = env.get("LBANK_API_SECRET", "")
    signature_method = env.get("LBANK_SIGNATURE_METHOD", "HmacSHA256")

    print(f"api_key: {'set' if api_key else 'missing'} length={len(api_key)}")
    print(f"api_secret: {'set' if api_secret else 'missing'} length={len(api_secret)}")
    print(f"base_url: {base_url}")

    status, body = _get_json(f"{base_url}/cfd/openApi/v1/pub/getTime")
    print(f"public getTime: HTTP {status} {body[:120]}")

    if not api_key or not api_secret:
        print("private prv/account: skipped, missing key/secret")
        return 2

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
    print(f"private prv/account: HTTP {status} {text[:160]}")
    return 0 if status == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
