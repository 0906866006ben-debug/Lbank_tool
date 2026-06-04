"""Push a sanitized widget snapshot from a desktop backend to the public backend.

The desktop backend can hold LBank credentials and call LBank from the user's
home IP. The public backend only receives the already-shaped WidgetSummary.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request


def _json_get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _json_post(url: str, token: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Sync-Token": token,
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def push_once(source_url: str, target_base_url: str, token: str) -> None:
    payload = _json_get(source_url)
    target_url = target_base_url.rstrip("/") + "/api/lbank/widget-snapshot"
    result = _json_post(target_url, token, payload)
    print(
        "pushed",
        result.get("updated_at", "--"),
        f"positions={len(result.get('positions', []))}",
        flush=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-url",
        default="http://127.0.0.1:8000/api/lbank/widget-summary",
        help="Desktop backend widget-summary URL.",
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Public backend base URL, for example https://lbanktool-production.up.railway.app",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("LBANK_SYNC_TOKEN", ""),
        help="Sync token. Prefer LBANK_SYNC_TOKEN environment variable.",
    )
    parser.add_argument("--interval", type=int, default=0, help="Repeat every N seconds.")
    args = parser.parse_args()

    if not args.token:
        print("LBANK_SYNC_TOKEN is required.", file=sys.stderr)
        return 2

    while True:
        try:
            push_once(args.source_url, args.target, args.token)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            print(f"sync failed: {exc}", file=sys.stderr, flush=True)
        if args.interval <= 0:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
