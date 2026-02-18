# Platform Stack Architecture

**Sprint:** PROCLAMATIO
**Date:** 2026-02-17
**Owner:** ORGAN-VII (Kerygma)

## Overview

The organvm creative technologist platform stack is designed around the POSSE principle: **Publish (on your) Own Site, Syndicate Everywhere**. Ghost serves as the canonical publishing hub, with automated syndication to social platforms via the kerygma pipeline.

## Full Stack

| Layer | Platform | Purpose | Status |
|-------|----------|---------|--------|
| **Hub** | Ghost | Canonical publishing, newsletter, membership | Active |
| **Fediverse** | Mastodon (via Ghost ActivityPub) | Open social web presence | Active |
| **Social** | Bluesky | "Town square" — writers/artists community | Active |
| **Social** | Discord | Community server, real-time discussion | Active |
| **Visual** | Instagram | Visual portfolio / gallery | Manual |
| **Professional** | Read.cv | Creative technologist identity | Manual |
| **Inspiration** | Are.na | Research / mood boarding | Manual |
| **Code** | GitHub | Source, process, building in public | Active |
| **Landing** | Bento.me (or Ghost homepage) | Link-in-bio / landing page | Planned |

## Data Flow

```
                    ┌─────────────────────────────┐
                    │         Ghost (Hub)          │
                    │  Newsletter · Blog · CMS     │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────┴──────────────────┐
                    │      ActivityPub (native)    │
                    │  Auto-federates to Fediverse │
                    └──────────┬──────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                     │
          ▼                    ▼                     ▼
   ┌─────────────┐    ┌──────────────┐     ┌──────────────┐
   │  Mastodon    │    │   Discord    │     │   Bluesky    │
   │  (POSSE +   │    │  (webhook)   │     │  (AT Proto)  │
   │  ActivityPub)│    └──────────────┘     └──────────────┘
   └─────────────┘
```

## Automated vs Manual Channels

**Automated (kerygma pipeline):**
- Ghost — Admin API with JWT auth
- Mastodon — OAuth access token
- Discord — Webhook URL
- Bluesky — AT Protocol with app password

**Manual (human-curated):**
- Instagram — Visual content requires manual curation
- Read.cv — Professional profile, infrequent updates
- Are.na — Research collecting, organic process
- Landing page — Updated periodically

## Ghost as Canonical Hub

Ghost serves three distinct roles:

1. **Newsletter delivery** — Email subscribers receive new posts directly
2. **Headless CMS** — Content API enables custom frontends and integrations
3. **Fediverse presence** — Native ActivityPub makes the instance followable from Mastodon, Threads, Flipboard, and other compatible platforms

### POSSE Interaction

For **newsletter/essay content**: Ghost publishes canonically, and the kerygma pipeline syndicates shorter announcements to Mastodon, Discord, and Bluesky with back-links.

For **short-form announcements**: The kerygma pipeline creates Ghost posts (as drafts or published) alongside social media posts, maintaining Ghost as the canonical archive.

Ghost's ActivityPub federation means Mastodon followers see full newsletter content natively, while the POSSE Mastodon channel provides supplementary short-form engagement.

## Security Model

| Platform | Auth Method | Secret Name |
|----------|-------------|-------------|
| Ghost | JWT (HS256) via Admin API key | `KERYGMA_GHOST_ADMIN_API_KEY` |
| Mastodon | OAuth access token | `KERYGMA_MASTODON_ACCESS_TOKEN` |
| Discord | Webhook URL (contains token) | `KERYGMA_DISCORD_WEBHOOK_URL` |
| Bluesky | App password | `KERYGMA_BLUESKY_APP_PASSWORD` |

All secrets are stored as GitHub repository secrets and injected via environment variables at workflow runtime.
