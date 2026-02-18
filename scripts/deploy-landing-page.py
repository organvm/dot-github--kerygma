#!/usr/bin/env python3
"""Create or update the ORGANVM landing page on Ghost via Admin API.

Usage:
    KERYGMA_GHOST_API_URL=... KERYGMA_GHOST_ADMIN_API_KEY=... python scripts/deploy-landing-page.py
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.request
import urllib.error
from base64 import urlsafe_b64encode


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


LANDING_HTML = """
<div style="text-align: center; padding: 2rem 0;">
    <h1 style="font-size: 2.5rem; letter-spacing: 0.05em; color: #c9a84c;">ORGANVM</h1>
    <p style="font-size: 1.2rem; color: #888;">Eight organs. One system. A creative technologist's institutional architecture.</p>
</div>

<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; max-width: 900px; margin: 2rem auto;">
    <div style="background: #1a1a1a; border-left: 3px solid #7b68ee; padding: 1rem; border-radius: 8px;">
        <strong style="color: #7b68ee;">I. Theoria</strong><br>
        <span style="color: #888;">Philosophy &amp; Recursive Frameworks</span>
    </div>
    <div style="background: #1a1a1a; border-left: 3px solid #ff6b9d; padding: 1rem; border-radius: 8px;">
        <strong style="color: #ff6b9d;">II. Poiesis</strong><br>
        <span style="color: #888;">Art, Music &amp; Creative Technology</span>
    </div>
    <div style="background: #1a1a1a; border-left: 3px solid #4ecdc4; padding: 1rem; border-radius: 8px;">
        <strong style="color: #4ecdc4;">III. Ergon</strong><br>
        <span style="color: #888;">Software Engineering &amp; Products</span>
    </div>
    <div style="background: #1a1a1a; border-left: 3px solid #f9a825; padding: 1rem; border-radius: 8px;">
        <strong style="color: #f9a825;">IV. Taxis</strong><br>
        <span style="color: #888;">Orchestration &amp; System Governance</span>
    </div>
    <div style="background: #1a1a1a; border-left: 3px solid #42a5f5; padding: 1rem; border-radius: 8px;">
        <strong style="color: #42a5f5;">V. Logos</strong><br>
        <span style="color: #888;">Essays &amp; Public Process</span>
    </div>
    <div style="background: #1a1a1a; border-left: 3px solid #66bb6a; padding: 1rem; border-radius: 8px;">
        <strong style="color: #66bb6a;">VI. Koinonia</strong><br>
        <span style="color: #888;">Community &amp; Collaboration</span>
    </div>
    <div style="background: #1a1a1a; border-left: 3px solid #ab47bc; padding: 1rem; border-radius: 8px;">
        <strong style="color: #ab47bc;">VII. Kerygma</strong><br>
        <span style="color: #888;">Distribution &amp; Proclamation</span>
    </div>
    <div style="background: #1a1a1a; border-left: 3px solid #c9a84c; padding: 1rem; border-radius: 8px;">
        <strong style="color: #c9a84c;">VIII. Meta</strong><br>
        <span style="color: #888;">System of Systems</span>
    </div>
</div>

<div style="text-align: center; margin: 3rem 0;">
    <p style="color: #888; margin-bottom: 1rem;">Subscribe to follow the build in public.</p>
    <div data-ghost-portal="signup" style="display: inline-block; background: #c9a84c; color: #0d0d0d; padding: 0.6rem 2rem; border-radius: 4px; font-weight: 600; cursor: pointer;">Subscribe</div>
</div>

<div style="text-align: center; margin: 2rem 0; display: flex; justify-content: center; gap: 1.5rem;">
    <a href="https://github.com/meta-organvm" style="color: #888;">GitHub</a>
    <a href="https://mastodon.social/@organvm" style="color: #888;">Mastodon</a>
    <a href="https://bsky.app/profile/organvm" style="color: #888;">Bluesky</a>
</div>
""".strip()


def main() -> int:
    api_url = os.environ.get("KERYGMA_GHOST_API_URL", "")
    api_key = os.environ.get("KERYGMA_GHOST_ADMIN_API_KEY", "")  # allow-secret — env var read

    if not api_url or not api_key:
        print("Set KERYGMA_GHOST_API_URL and KERYGMA_GHOST_ADMIN_API_KEY env vars.")
        return 1

    token = _build_jwt(api_key)  # allow-secret
    url = f"{api_url}/ghost/api/admin/pages/"

    body = json.dumps({
        "pages": [{
            "title": "Welcome to ORGANVM",
            "html": LANDING_HTML,
            "status": "published",
            "slug": "home",
            "custom_template": "",
        }],
    }).encode()

    req = urllib.request.Request(
        url, data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Ghost {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            page_url = result.get("pages", [{}])[0].get("url", "")
            print(f"Landing page created: {page_url}")
            print("Set this as your homepage in Ghost Admin > Settings > General > Homepage.")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"Ghost API error ({exc.code}): {error_body}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
