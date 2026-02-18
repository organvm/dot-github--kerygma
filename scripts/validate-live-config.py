#!/usr/bin/env python3
"""Validate live API connectivity for all configured kerygma platforms.

Checks each endpoint with a read-only request (no posting).
Exit 0 = all configured endpoints reachable.
Exit 1 = at least one endpoint unreachable.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request
from base64 import urlsafe_b64encode


def check_endpoint(name: str, url: str, headers: dict[str, str]) -> bool:
    """Send a GET/HEAD request and return True if we get a 2xx response."""
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"  [{name}] OK — HTTP {resp.status}")
            return True
    except Exception as exc:
        print(f"  [{name}] FAIL — {exc}")
        return False


def _ghost_jwt(api_key: str) -> str:  # allow-secret — JWT builder, no stored credentials
    key_id, secret_hex = api_key.split(":")
    header = json.dumps({"alg": "HS256", "typ": "JWT", "kid": key_id}, separators=(",", ":"))
    now = int(time.time())
    payload = json.dumps({"iat": now, "exp": now + 300, "aud": "/admin/"}, separators=(",", ":"))

    def b64(data: bytes) -> str:
        return urlsafe_b64encode(data).rstrip(b"=").decode()

    signing_input = f"{b64(header.encode())}.{b64(payload.encode())}"
    sig = hmac.new(bytes.fromhex(secret_hex), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{b64(sig)}"  # allow-secret — runtime JWT


def build_checks() -> list[tuple[str, str, dict[str, str]]]:
    """Build list of (name, url, headers) checks from environment."""
    checks: list[tuple[str, str, dict[str, str]]] = []

    ghost_url = os.environ.get("KERYGMA_GHOST_API_URL", "")
    ghost_key = os.environ.get("KERYGMA_GHOST_ADMIN_API_KEY", "")
    if ghost_url and ghost_key:
        token = _ghost_jwt(ghost_key)  # allow-secret
        checks.append(("Ghost", f"{ghost_url}/ghost/api/admin/site/", {"Authorization": f"Ghost {token}"}))

    masto_url = os.environ.get("KERYGMA_MASTODON_INSTANCE_URL", "")
    masto_token = os.environ.get("KERYGMA_MASTODON_ACCESS_TOKEN", "")
    if masto_url and masto_token:
        checks.append(("Mastodon", f"{masto_url}/api/v1/apps/verify_credentials",
                        {"Authorization": f"Bearer {masto_token}"}))

    discord_url = os.environ.get("KERYGMA_DISCORD_WEBHOOK_URL", "")
    if discord_url:
        checks.append(("Discord", discord_url, {}))

    bsky_handle = os.environ.get("KERYGMA_BLUESKY_HANDLE", "")
    if bsky_handle:
        checks.append(("Bluesky", "https://bsky.social/xrpc/com.atproto.server.describeServer", {}))

    return checks


def main() -> int:
    print("Kerygma Live Config Validation")
    print("=" * 40)
    checks = build_checks()
    if not checks:
        print("No platforms configured (set KERYGMA_* env vars).")
        return 1

    results = []
    for name, url, headers in checks:
        results.append(check_endpoint(name, url, headers))

    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} endpoints reachable.")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
