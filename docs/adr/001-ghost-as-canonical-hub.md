# ADR-001: Ghost as Canonical Publishing Hub

**Status:** Accepted
**Date:** 2026-02-17
**Sprint:** PROCLAMATIO

## Context

ORGAN-VII (Kerygma) needed a canonical publishing hub for the eight-organ system's external communication. The existing POSSE pipeline distributed content to Mastodon, Discord, and Bluesky, but lacked a long-form newsletter/blog platform that could serve as the authoritative source.

Requirements:
- Full visual control (custom themes, CSS, responsive galleries)
- Newsletter/membership support
- Headless CMS mode (Content API for custom frontends)
- Fediverse integration (ActivityPub)
- Open source and self-hostable
- No revenue fees on memberships

## Decision

**Ghost** is the canonical publishing hub for the organvm system.

The POSSE flow becomes:
1. **Ghost** (canonical) — long-form essays, newsletters, membership content
2. **Mastodon** (syndication) — short-form announcements, social engagement
3. **Discord** (syndication) — community discussion, real-time updates
4. **Bluesky** (syndication) — "town square" presence among writers/artists

Ghost's native **ActivityPub** integration makes the newsletter a followable Fediverse profile, meaning publishing to Ghost automatically federates content to Mastodon followers, Threads, Flipboard, and other compatible platforms.

## Rationale

| Criterion | Ghost | Substack | Buttondown |
|-----------|-------|----------|------------|
| Visual control | Full theme + CSS | Limited | Minimal |
| Headless CMS | Content API | No | API only |
| ActivityPub | Native | No | No |
| Revenue fees | 0% | 10% | 0% (paid tier) |
| Open source | Yes | No | No |
| Self-hostable | Yes | No | No |

Ghost uniquely combines newsletter delivery, headless CMS capability, and native Fediverse federation in a single open-source platform.

## Consequences

- Ghost Admin API key required as a repository secret (`KERYGMA_GHOST_ADMIN_API_KEY`)
- Ghost adapter added to `kerygma_social` package with JWT (HS256) authentication
- All 15 announcement templates now include `{{#channel ghost}}` blocks
- Ghost channel added to default pipeline distribution targets
- For newsletter content, Ghost ActivityPub federation supplements (not replaces) the Mastodon POSSE channel, since the two serve different content formats

## Related

- `social-automation/kerygma_social/ghost.py` — Ghost adapter implementation
- `announcement-templates/templates/` — All 15 templates with ghost channel blocks
- `kerygma_pipeline.py` — Pipeline with Ghost wired in
