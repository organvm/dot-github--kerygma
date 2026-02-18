#!/usr/bin/env python3
"""Sync GitHub org descriptions to reference the Ghost hub URL.

Usage:
    GHOST_HUB_URL=https://your-ghost.com python scripts/sync-platform-profiles.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys


ORGS = [
    "organvm-i-theoria",
    "organvm-ii-poiesis",
    "organvm-iii-ergon",
    "organvm-iv-taxis",
    "organvm-v-logos",
    "organvm-vi-koinonia",
    "organvm-vii-kerygma",
    "meta-organvm",
]


def update_org_blog(org: str, hub_url: str) -> bool:
    """Update org's blog field to point to Ghost hub URL."""
    result = subprocess.run(
        ["gh", "api", f"orgs/{org}", "-X", "PATCH", "-f", f"blog={hub_url}"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"  [{org}] blog → {hub_url}")
        return True
    else:
        print(f"  [{org}] FAIL: {result.stderr.strip()}")
        return False


def main() -> int:
    hub_url = os.environ.get("GHOST_HUB_URL", "")
    if not hub_url:
        print("Set GHOST_HUB_URL environment variable.")
        return 1

    print(f"Syncing all org profiles to hub: {hub_url}")
    results = []
    for org in ORGS:
        results.append(update_org_blog(org, hub_url))

    passed = sum(results)
    print(f"\n{passed}/{len(ORGS)} orgs updated.")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
