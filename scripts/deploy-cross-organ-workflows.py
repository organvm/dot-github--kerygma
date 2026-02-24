#!/usr/bin/env python3
"""Deploy cross-organ workflow templates to target repositories.

Reads workflow specs from docs/cross-organ-workflows/ and copies them
to target repos declared in each template's header comment.

Usage:
    python deploy-cross-organ-workflows.py              # dry-run (list targets)
    python deploy-cross-organ-workflows.py --deploy      # actually copy files
"""
from __future__ import annotations

import argparse
import logging
import re
import shutil
import sys
from pathlib import Path

logger = logging.getLogger("kerygma.deploy-workflows")

SCRIPT_DIR = Path(__file__).resolve().parent
GITHUB_ROOT = SCRIPT_DIR.parent
TEMPLATES_DIR = GITHUB_ROOT / "docs" / "cross-organ-workflows"
WORKSPACE = Path.home() / "Workspace"


def parse_template(path: Path) -> dict:
    """Parse a workflow template to extract deploy target and metadata.

    Looks for a header comment like:
      # Deploy this to: organvm-v-logos/public-process/.github/workflows/notify-essay-published.yml
    or:
      # Target repos: public-record-data-scrapper, fetch-familiar-friends, tab-bookmark-manager
    """
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    result = {
        "source": path,
        "filename": path.name,
        "content": content,
        "deploy_to": [],
        "target_repos": [],
    }

    for line in lines:
        # Direct deploy path (skip descriptive comments like "any ORGAN-III repo's")
        match = re.match(r"^#\s*Deploy this to:\s*(.+)", line, re.IGNORECASE)
        if match:
            deploy_path = match.group(1).strip()
            # Only treat as a real path if it looks like org/repo/path (has /)
            # and isn't a generic description (contains "any")
            if "/" in deploy_path and "any " not in deploy_path.lower():
                result["deploy_to"].append(deploy_path)

        # Target repos list (for templates that apply to multiple repos)
        match = re.match(r"^#\s*Target repos:\s*(.+)", line, re.IGNORECASE)
        if match:
            repos = [r.strip() for r in match.group(1).split(",")]
            result["target_repos"] = repos

    return result


def resolve_deploy_targets(template: dict) -> list[Path]:
    """Resolve all deploy target paths for a template."""
    targets: list[Path] = []

    # Direct deploy paths
    for deploy_path in template["deploy_to"]:
        full_path = WORKSPACE / deploy_path
        targets.append(full_path)

    # Target repos (need to construct the workflow path from template name)
    for repo_name in template["target_repos"]:
        # Search for the repo in workspace organ directories
        for organ_dir in WORKSPACE.iterdir():
            if not organ_dir.is_dir() or not organ_dir.name.startswith("organvm-"):
                continue
            repo_path = organ_dir / repo_name
            if repo_path.is_dir():
                workflow_dir = repo_path / ".github" / "workflows"
                targets.append(workflow_dir / template["filename"])
                break

    return targets


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Deploy cross-organ workflow templates",
    )
    parser.add_argument(
        "--deploy", action="store_true",
        help="Actually copy workflow files (default: dry-run)",
    )
    args = parser.parse_args()

    if not TEMPLATES_DIR.exists():
        logger.error("Templates directory not found: %s", TEMPLATES_DIR)
        return 1

    templates = list(TEMPLATES_DIR.glob("*.yml"))
    if not templates:
        logger.info("No workflow templates found in %s", TEMPLATES_DIR)
        return 0

    logger.info("Cross-Organ Workflow Deployment")
    logger.info("=" * 50)
    logger.info("Source: %s", TEMPLATES_DIR)
    logger.info("Mode: %s", "DEPLOY" if args.deploy else "DRY-RUN")
    logger.info("")

    total_targets = 0
    deployed = 0

    for template_path in sorted(templates):
        template = parse_template(template_path)
        targets = resolve_deploy_targets(template)

        logger.info("Template: %s", template["filename"])
        if not targets:
            logger.info("  No deploy targets found")
            continue

        for target in targets:
            total_targets += 1
            exists = target.exists()
            status = "EXISTS" if exists else "NEW"

            if args.deploy:
                target.parent.mkdir(parents=True, exist_ok=True)
                # Strip the header comments (deploy instructions) from the copy
                content = template["content"]
                clean_lines = []
                for line in content.splitlines():
                    if line.startswith("# Deploy this to:") or line.startswith("# Target repos:"):
                        continue
                    clean_lines.append(line)
                target.write_text("\n".join(clean_lines), encoding="utf-8")
                deployed += 1
                logger.info("  [DEPLOYED] %s", target)
            else:
                logger.info("  [%s] %s", status, target)

    logger.info("")
    logger.info("Summary: %d targets, %d deployed", total_targets, deployed)
    if not args.deploy and total_targets > 0:
        logger.info("Run with --deploy to copy files.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
