# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

The `.github` org-level repository for ORGAN-VII (Kerygma). Contains CI/CD workflows, the pipeline orchestrator script, operational deployment scripts, a Ghost newsletter theme, cross-organ workflow specs, community health files, and the authoritative `seed.yaml` for the entire organ.

## Repository Structure

| Path | Purpose |
|------|---------|
| `.github/workflows/` | 8 GitHub Actions workflows (CI, dispatch, RSS polling, analytics, quarterly) |
| `scripts/` | Operational Python scripts for deployment and validation |
| `docs/` | ADRs, cross-organ workflow YAML specs, platform stack docs |
| `docs/cross-organ-workflows/` | Reusable workflow specs (`notify-essay-published.yml`, `notify-feature-released.yml`) |
| `organvm-theme/` | Ghost newsletter Handlebars theme (`default.hbs`, `index.hbs`, `post.hbs`, `partials/`, `assets/`) |
| `tests/` | Integration tests for pipeline and config validation |
| `kerygma_pipeline.py` | Pipeline orchestrator (same file as in `kerygma-pipeline/` submodule) |
| `kerygma_config.example.yaml` | Reference configuration for all platforms, channels, calendar |
| `seed.yaml` | Authoritative organ contract — declares all packages, event subscriptions (13 inbound from 6 organs), produced events, platform stack, channels, fediverse config |
| `organ-aesthetic.yaml` | Visual identity modifiers (palette, typography, tone) |

## CI/CD Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci-pipeline.yml` | push to main | Install all packages, run tests |
| `dispatch-receiver.yml` | `repository_dispatch` | Receives cross-organ events, runs full pipeline |
| `rss-auto-dispatch.yml` | cron (every 6h) | Polls ORGAN-V Atom feed, dispatches new essays |
| `weekly-analytics.yml` | cron (Monday 09:00 UTC) | Generates weekly distribution report as GitHub issue |
| `dispatch-log.yml` | — | Dispatch activity logging |
| `notify-kerygma.yml` | — | Cross-organ notification handler |
| `quarterly-feedback.yml` | — | Quarterly feedback collection (Edge 6: VII→I) |
| `quarterly-synthesis-dispatch.yml` | — | Quarterly synthesis broadcast |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/deploy-ghost-theme.py` | Deploys `organvm-theme/` to Ghost instance via Admin API |
| `scripts/deploy-landing-page.py` | Deploys landing page content |
| `scripts/sync-platform-profiles.py` | Syncs profile info across platforms |
| `scripts/update-status-badge.py` | Updates `docs/status-badge.json` |
| `scripts/validate-live-config.py` | Validates `kerygma_config.yaml` has required credentials before live dispatch |

## Development Commands

```bash
# Tests (from superproject root, needs all three packages installed)
pytest .github/tests/ -v

# Validate config
python .github/scripts/validate-live-config.py
```

## Key Details

- **seed.yaml is the authoritative organ contract** — declares all 4 packages, 13 inbound event subscriptions from 6 organs, 4 produced events, the full platform stack (Ghost hub + Mastodon/Bluesky/Discord social + manual channels), and fediverse/ActivityPub integration via Ghost.
- **Ghost theme** in `organvm-theme/` uses Handlebars (`.hbs`). Deployed via `scripts/deploy-ghost-theme.py` using Ghost Admin API JWT auth.
- **Cross-organ workflows** in `docs/cross-organ-workflows/` are YAML specs that other organs' `dispatch-receiver` workflows consume.
- Community health files: `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/`.

<!-- ORGANVM:AUTO:START -->
## System Context (auto-generated — do not edit)

**Organ:** ORGAN-I (Theory) | **Tier:** infrastructure | **Status:** LOCAL
**Org:** `unknown` | **Repo:** `.github`

### Edges
- **Produces** → `unknown`: unknown (event: `distribution-completed`)
- **Produces** → `unknown`: unknown (event: `press-release`)
- **Produces** → `unknown`: unknown (event: `grant-update`)
- **Produces** → `unknown`: unknown (event: `newsletter-published`)

### Siblings in Theory
`recursive-engine--generative-entity`, `organon-noumenon--ontogenetic-morphe`, `auto-revision-epistemic-engine`, `narratological-algorithmic-lenses`, `call-function--ontological`, `sema-metra--alchemica-mundi`, `system-governance-framework`, `cognitive-archaelogy-tribunal`, `a-recursive-root`, `radix-recursiva-solve-coagula-redi`, `nexus--babel-alexandria-`, `reverse-engine-recursive-run`, `4-ivi374-F0Rivi4`, `cog-init-1-0-`, `collective-persona-operations` ... and 4 more

### Governance
- Foundational theory layer. No upstream dependencies.

*Last synced: 2026-02-24T12:41:28Z*
<!-- ORGANVM:AUTO:END -->
