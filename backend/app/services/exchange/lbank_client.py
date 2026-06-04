"""Thin HTTP client for LBank read-only requests.

This client only knows how to send a *signed read-only* request. It has no
trading methods. It is NOT used on the first-version main line (mock mode);
it exists so the RealLBankAdapter has a signing-aware transport once a
verified read-only Futures endpoint is available.

SECURITY:
  - The secret is used only to compute the signature and is never logged.
  - Responses are returned as-is to the caller; the caller (adapter) must
    map only non-sensitive fields into widget models.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping

import httpx

from app.config import Settings, get_settings
from app.services.exchange.lbank_signer import sign_request


class LBankClient:
    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()

    def _signed_body(self, params: Mapping[str, object]) -> Dict[str, str]:
        if not self._settings.api_secret:
            raise RuntimeError("No API secret configured for signed request.")
        return sign_request(
            params,
            self._settings.api_secret,
            signature_method=self._settings.signature_method,
        )

    def get_signed(self, path: str, params: Mapping[str, object]) -> Any:
        """POST a signed, read-only request (LBank uses form-encoded POST for
        signed calls). `path` must be a verified read-only endpoint.

        TODO(unverified-endpoint): callers must only pass confirmed
        read-only paths. This method does not and must not call trading
        endpoints.
        """
        body = self._signed_body(params)
        body["api_key"] = self._settings.api_key
        url = self._settings.base_url.rstrip("/") + "/" + path.lstrip("/")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = httpx.post(url, data=body, headers=headers, timeout=10.0)
        resp.raise_for_status()
        return resp.json()
