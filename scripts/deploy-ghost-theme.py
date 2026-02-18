#!/usr/bin/env python3
"""Deploy the organvm Ghost theme by zipping and uploading to Ghost Admin API.

Usage:
    KERYGMA_GHOST_API_URL=... KERYGMA_GHOST_ADMIN_API_KEY=... python scripts/deploy-ghost-theme.py
"""
from __future__ import annotations

import hashlib
import hmac
import io
import json
import os
import sys
import time
import zipfile
import urllib.request
import urllib.error
from base64 import urlsafe_b64encode
from pathlib import Path


def _build_jwt(api_key: str) -> str:  # allow-secret — JWT builder, no stored credentials
    key_id, secret_hex = api_key.split(":")
    header = json.dumps({"alg": "HS256", "typ": "JWT", "kid": key_id}, separators=(",", ":"))
    now = int(time.time())
    payload = json.dumps({"iat": now, "exp": now + 300, "aud": "/admin/"}, separators=(",", ":"))

    def b64(data: bytes) -> str:
        return urlsafe_b64encode(data).rstrip(b"=").decode()

    signing_input = f"{b64(header.encode())}.{b64(payload.encode())}"
    sig = hmac.new(bytes.fromhex(secret_hex), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{b64(sig)}"  # allow-secret — runtime JWT


def zip_theme(theme_dir: Path) -> bytes:
    """Create a ZIP archive of the theme directory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(theme_dir.rglob("*")):
            if path.is_file() and not path.name.startswith("."):
                arcname = path.relative_to(theme_dir.parent)
                zf.write(path, arcname)
    return buf.getvalue()


def upload_theme(api_url: str, api_key: str, theme_zip: bytes) -> dict:  # allow-secret
    """Upload theme ZIP to Ghost Admin API."""
    token = _build_jwt(api_key)  # allow-secret
    url = f"{api_url}/ghost/api/admin/themes/upload/"
    boundary = "----OrganvmThemeBoundary"

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="organvm-theme.zip"\r\n'
        f"Content-Type: application/zip\r\n\r\n"
    ).encode() + theme_zip + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Ghost {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ghost theme upload failed ({exc.code}): {error_body}") from exc


def main() -> int:
    api_url = os.environ.get("KERYGMA_GHOST_API_URL", "")
    api_key = os.environ.get("KERYGMA_GHOST_ADMIN_API_KEY", "")  # allow-secret — env var read

    if not api_url or not api_key:
        print("Set KERYGMA_GHOST_API_URL and KERYGMA_GHOST_ADMIN_API_KEY env vars.")
        return 1

    theme_dir = Path(__file__).parent.parent / "organvm-theme"
    if not theme_dir.is_dir():
        print(f"Theme directory not found: {theme_dir}")
        return 1

    print(f"Zipping theme from {theme_dir}...")
    theme_zip = zip_theme(theme_dir)
    print(f"  ZIP size: {len(theme_zip):,} bytes")

    print(f"Uploading to {api_url}...")
    result = upload_theme(api_url, api_key, theme_zip)
    theme_name = result.get("themes", [{}])[0].get("name", "unknown")
    print(f"  Theme uploaded: {theme_name}")
    print("  Activate it in Ghost Admin > Settings > Design.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
