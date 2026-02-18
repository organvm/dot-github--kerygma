#!/usr/bin/env python3
"""Update the shields.io endpoint badge JSON after each dispatch.

Reads the dispatch log to count total dispatches and calculate
the 7-day success rate, then writes docs/status-badge.json.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


def count_dispatches(log_path: Path) -> tuple[int, int]:
    """Count total and recent (7-day) dispatches from dispatch-log.md.

    Returns (total, recent_7d).
    """
    if not log_path.exists():
        return 0, 0

    total = 0
    recent = 0
    cutoff = datetime.utcnow() - timedelta(days=7)

    for line in log_path.read_text().splitlines():
        if not line.startswith("|") or "Timestamp" in line or "---" in line:
            continue
        total += 1
        match = re.match(r"\|\s*(\d{4}-\d{2}-\d{2})", line)
        if match:
            try:
                ts = datetime.strptime(match.group(1), "%Y-%m-%d")
                if ts >= cutoff:
                    recent += 1
            except ValueError:
                pass

    return total, recent


def main() -> None:
    docs_dir = Path(__file__).parent.parent / "docs"
    log_path = docs_dir / "dispatch-log.md"
    badge_path = docs_dir / "status-badge.json"

    total, recent = count_dispatches(log_path)

    if total == 0:
        message = "operational — 0 dispatches"
        color = "green"
    else:
        message = f"operational — {total} dispatches ({recent} this week)"
        color = "brightgreen" if recent > 0 else "green"

    badge = {
        "schemaVersion": 1,
        "label": "kerygma pipeline",
        "message": message,
        "color": color,
    }

    badge_path.write_text(json.dumps(badge, indent=2) + "\n")
    print(f"Badge updated: {message}")


if __name__ == "__main__":
    main()
