#!/usr/bin/env python3
"""First-fire pre-flight check — comprehensive operational readiness dashboard.

Runs all validation steps needed before the first live dispatch:
  1. Pipeline activate (template + event map checks)
  2. Live config connectivity (validate-live-config.py)
  3. Dry-run dispatch for each configured platform
  4. Go/no-go dashboard

Usage:
    python first-fire.py           # dry-run pre-flight only
    python first-fire.py --live    # execute the actual first dispatch
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("kerygma.first-fire")

# Resolve paths relative to the .github submodule root
SCRIPT_DIR = Path(__file__).resolve().parent
GITHUB_ROOT = SCRIPT_DIR.parent
SUPERPROJECT_ROOT = GITHUB_ROOT.parent


def run_activate() -> dict:
    """Run pipeline activate command and return the structured report."""
    logger.info("=" * 60)
    logger.info("STEP 1: Pipeline Activate (pre-flight checks)")
    logger.info("=" * 60)

    try:
        # Import from the kerygma-pipeline package
        sys.path.insert(0, str(SUPERPROJECT_ROOT / "kerygma-pipeline"))
        from kerygma_pipeline import KerygmaPipeline

        templates_dir = SUPERPROJECT_ROOT / "announcement-templates" / "templates"
        pipeline = KerygmaPipeline(templates_dir=templates_dir)
        report = pipeline.activate()
        for key, value in report.items():
            status = "OK" if value else "FAIL" if isinstance(value, bool) else value
            logger.info("  %-25s %s", key, status)
        return report
    except Exception as exc:
        logger.error("  Activate failed: %s", exc)
        return {"ready": False, "error": str(exc)}


def run_connectivity_check() -> bool:
    """Run validate-live-config.py connectivity check."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("STEP 2: Live Config Connectivity")
    logger.info("=" * 60)

    validate_script = SCRIPT_DIR / "validate-live-config.py"
    if not validate_script.exists():
        logger.error("  validate-live-config.py not found at %s", validate_script)
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(validate_script)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        for line in result.stdout.splitlines():
            logger.info("  %s", line)
        for line in result.stderr.splitlines():
            logger.warning("  %s", line)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.error("  Connectivity check timed out")
        return False
    except Exception as exc:
        logger.error("  Connectivity check failed: %s", exc)
        return False


def run_dry_dispatch() -> dict[str, bool]:
    """Run a dry-run dispatch for each channel to verify the full path."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("STEP 3: Dry-Run Dispatch (all channels)")
    logger.info("=" * 60)

    results: dict[str, bool] = {}
    channels = ["mastodon", "discord", "bluesky", "ghost"]

    try:
        sys.path.insert(0, str(SUPERPROJECT_ROOT / "kerygma-pipeline"))
        from kerygma_pipeline import KerygmaPipeline

        templates_dir = SUPERPROJECT_ROOT / "announcement-templates" / "templates"
        pipeline = KerygmaPipeline(templates_dir=templates_dir)

        for channel in channels:
            try:
                channel_texts = pipeline.render_and_check(
                    "essay-announce", "public-process", [channel],
                )
                if channel in channel_texts:
                    records = pipeline.dispatch({channel: channel_texts[channel]})
                    status = any(r["status"] in ("published", "skipped") for r in records)
                    results[channel] = status
                    logger.info("  %-12s %s", channel, "OK (rendered + dispatched)" if status else "FAIL")
                else:
                    results[channel] = False
                    logger.info("  %-12s SKIP (quality check failed or no template)", channel)
            except Exception as exc:
                results[channel] = False
                logger.info("  %-12s FAIL (%s)", channel, exc)
    except Exception as exc:
        logger.error("  Dry-run dispatch setup failed: %s", exc)

    return results


def display_dashboard(
    activate_report: dict,
    connectivity_ok: bool,
    dispatch_results: dict[str, bool],
) -> bool:
    """Display the go/no-go dashboard. Returns True if all checks pass."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("DASHBOARD: Go/No-Go Summary")
    logger.info("=" * 60)

    checks = {
        "Templates loaded": activate_report.get("templates_ok", False),
        "Event map complete": activate_report.get("event_map_ok", False),
        "Sample render OK": activate_report.get("sample_render_ok", False),
        "Platform(s) configured": activate_report.get("social_config_ok", False),
        "Connectivity check": connectivity_ok,
    }

    for channel, ok in dispatch_results.items():
        checks[f"Dry-run: {channel}"] = ok

    all_critical_pass = all([
        checks["Templates loaded"],
        checks["Event map complete"],
        checks["Sample render OK"],
    ])

    for name, passed in checks.items():
        icon = "PASS" if passed else "FAIL"
        logger.info("  [%s] %s", icon, name)

    logger.info("")
    if all_critical_pass and checks.get("Platform(s) configured"):
        logger.info("  VERDICT: GO — system is ready for live dispatch")
        return True
    elif all_critical_pass:
        logger.info("  VERDICT: PARTIAL — pipeline OK, but no platforms configured")
        logger.info("  Configure platform credentials (KERYGMA_* env vars) and re-run")
        return False
    else:
        logger.info("  VERDICT: NO-GO — critical checks failed")
        return False


def execute_first_dispatch() -> None:
    """Execute the actual first live dispatch."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("EXECUTING FIRST LIVE DISPATCH")
    logger.info("=" * 60)

    try:
        sys.path.insert(0, str(SUPERPROJECT_ROOT / "kerygma-pipeline"))
        from kerygma_pipeline import KerygmaPipeline

        templates_dir = SUPERPROJECT_ROOT / "announcement-templates" / "templates"
        pipeline = KerygmaPipeline(templates_dir=templates_dir)
        result = pipeline.run_full_pipeline(
            event_type="essay-published",
            repo_name="public-process",
            channels=["mastodon", "discord", "bluesky", "ghost"],
        )
        logger.info("  Result: %s", json.dumps(result, indent=2))
    except Exception as exc:
        logger.error("  First dispatch failed: %s", exc)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Kerygma first-fire operational readiness check",
    )
    parser.add_argument(
        "--live", action="store_true",
        help="Execute the actual first dispatch (requires all checks to pass)",
    )
    args = parser.parse_args()

    logger.info("KERYGMA FIRST-FIRE PRE-FLIGHT")
    logger.info("Date: %s", __import__("datetime").datetime.now().isoformat())
    logger.info("")

    # Step 1: Activate
    activate_report = run_activate()

    # Step 2: Connectivity
    connectivity_ok = run_connectivity_check()

    # Step 3: Dry-run dispatches
    dispatch_results = run_dry_dispatch()

    # Step 4: Dashboard
    go = display_dashboard(activate_report, connectivity_ok, dispatch_results)

    # Step 5: Live execution (if requested and checks pass)
    if args.live:
        if go:
            execute_first_dispatch()
        else:
            logger.error("Cannot execute --live: pre-flight checks did not pass")
            return 1

    return 0 if go else 1


if __name__ == "__main__":
    sys.exit(main())
