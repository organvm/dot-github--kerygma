# IGNIS PERPETUUS — Sprint Design

**Date:** 2026-02-18
**Status:** Approved
**Scope:** Full-system activation — live fire, cross-organ wiring, autonomous loop, public presence

## Problem

ORGAN-VII has 216 tests, 4 platform adapters, 15 templates, a full pipeline orchestrator, and resilience infrastructure. None of it has ever processed a real event. The system is a loaded cannon that has never been fired. Meanwhile, the other 7 organs have no mechanism to trigger distribution, and there is no public-facing presence tying the system together.

## Design

Four sequential phases, each enabling the next:

### Phase I: IGNITION — First Live Fire

**Goal:** First real content flowing through all 5 channels.

**Components:**

1. **Live config validation script** (`scripts/validate-live-config.py`)
   - Checks each API endpoint returns a valid response without posting
   - Ghost: `GET /ghost/api/admin/site/`
   - Mastodon: `GET /api/v1/apps/verify_credentials`
   - Discord: `HEAD` on webhook URL
   - Bluesky: `GET /xrpc/com.atproto.server.describeServer`
   - Exits non-zero if any endpoint unreachable

2. **GitHub secrets configuration** — Manual step, 6 secrets:
   - `KERYGMA_GHOST_API_URL`, `KERYGMA_GHOST_ADMIN_API_KEY`
   - `KERYGMA_MASTODON_ACCESS_TOKEN`
   - `KERYGMA_DISCORD_WEBHOOK_URL`
   - `KERYGMA_BLUESKY_HANDLE`, `KERYGMA_BLUESKY_APP_PASSWORD`

3. **First live dispatch** — CLI invocation in live mode:
   ```
   python kerygma_pipeline.py dispatch \
     --template essay-announce --repo public-process \
     --channels mastodon,discord,bluesky,ghost
   ```

4. **Delivery log verification** — Confirm all channels show `PUBLISHED`

**Success criteria:** Content appears on all 4 platforms with correct formatting.

### Phase II: NEXUS — Cross-Organ Nervous System

**Goal:** Other organs fire events into ORGAN-VII automatically.

**Components:**

1. **Reusable notify workflow** (`notify-kerygma.yml` upgrade)
   - `workflow_call` interface: `event_type`, `repo_name`, `channels` (optional, defaults to all)
   - Fires `repository_dispatch` to `organvm-vii-kerygma/.github`
   - Any organ can call it with 3 lines of YAML

2. **ORGAN-V essay trigger** — New workflow in `organvm-v-logos/public-process`:
   - Triggers on push to `_posts/` directory
   - Extracts essay metadata (title, URL from filename convention)
   - Calls notify-kerygma with `essay-published` event

3. **ORGAN-III release trigger** — New workflow template:
   - Triggers on `release: published`
   - Extracts release metadata (tag, notes, repo URL)
   - Calls notify-kerygma with `feature-released` event
   - Deploy to 2-3 key repos (public-record-data-scrapper, fetch-familiar-friends, tab-bookmark-manager)

4. **ORGAN-IV audit trigger** — Upgrade `monthly-organ-audit.yml`:
   - After successful audit, emit `audit-completed` dispatch
   - Payload includes audit summary metrics

5. **Dispatch log** — New workflow `dispatch-log.yml`:
   - Appends each received dispatch to `docs/dispatch-log.md` as a table row
   - Provides a running history of all cross-organ events

**Success criteria:** Push a new essay to ORGAN-V, watch it automatically appear on all platforms via ORGAN-VII.

### Phase III: AUTONOMIA — Self-Running Loop

**Goal:** The system monitors, distributes, and reports without human intervention.

**Components:**

1. **Cron RSS poller** — New workflow `rss-auto-dispatch.yml`:
   - Schedule: every 6 hours (`cron: '0 */6 * * *'`)
   - Runs `kerygma_pipeline.py poll` to check Ghost RSS feed
   - For each new entry, runs `kerygma_pipeline.py dispatch`
   - Uses delivery log deduplication to avoid double-posting

2. **Bidirectional analytics** — New modules in `kerygma_strategy`:
   - `mastodon_metrics.py`: Pull boosts, favorites, replies via `/api/v1/statuses/:id`
   - `ghost_metrics.py`: Pull email open rate, member count via Ghost Content API
   - `discord_metrics.py`: Parse webhook response headers for delivery confirmation
   - All follow existing adapter pattern (config dataclass, client with live/mock)

3. **Weekly analytics workflow** — `weekly-analytics.yml`:
   - Schedule: Monday 09:00 UTC
   - Pulls metrics from all platforms via new adapters
   - Writes aggregated data to `analytics.json`
   - Runs `kerygma_pipeline.py report --period weekly`
   - Creates GitHub issue with the Markdown report

4. **Status badge** — Dynamic SVG badge workflow:
   - Runs after each dispatch, updates `docs/status-badge.json`
   - Shows: last dispatch time, 7-day success rate, total dispatches
   - Referenced from org profile README

**Success criteria:** Leave the system alone for a week. It polls, distributes, pulls metrics, and generates a report issue — all autonomously.

### Phase IV: SPECTACULUM — The Public Face

**Goal:** Visitors arrive at a coherent, stunning creative technologist presence.

**Components:**

1. **Ghost theme** — Custom Handlebars theme (`organvm-theme/`):
   - Dark background, organ-specific accent colors
   - Responsive image galleries for portfolio pieces
   - Code syntax highlighting (Prism.js)
   - ActivityPub follow button and membership CTA
   - Mobile-first responsive design
   - Deploy via Ghost Admin API theme upload

2. **Ghost configuration** (manual admin steps):
   - Enable ActivityPub in Settings > Labs
   - Configure newsletter name, sender, design
   - Set up membership tiers if desired
   - Import existing essays from GitHub Pages as Ghost posts

3. **Landing page** — Ghost homepage or standalone:
   - Eight-organ visual map with links
   - Newsletter subscribe form
   - Selected works / portfolio grid
   - Social links (Mastodon, Bluesky, Discord, GitHub)
   - Minimal, high-contrast design

4. **Profile sync** — Update bios on all platforms to point to Ghost hub URL

**Success criteria:** A stranger can discover the organvm system, understand it, subscribe, and follow across platforms — all from a single entry point.

## Architecture

```
  ORGAN-I ─────┐
  ORGAN-II ────┤
  ORGAN-III ───┤  notify-kerygma.yml
  ORGAN-IV ────┤──(repository_dispatch)──► ORGAN-VII
  ORGAN-V ─────┤                          dispatch-receiver.yml
  ORGAN-VI ────┘                               │
                                               ▼
                                        kerygma_pipeline.py
                                     ┌────────┼────────┐
                                     ▼        ▼        ▼
                               render    quality    dispatch
                            (templates)  (checker)  (POSSE)
                                                  ┌──┬──┬──┐
                                                  ▼  ▼  ▼  ▼
                                               Ghost Masto Discord Bsky
                                                  │
                                          ┌───────┘
                                          ▼
                                    ActivityPub
                                   (auto-federate)
                                          │
                                    ┌─────┼─────┐
                                    ▼     ▼     ▼
                                 Masto Threads Flipboard

  ┌─── Autonomous loop ───┐
  │  cron (6h) ─► poll    │
  │  poll ─► dispatch     │
  │  weekly ─► analytics  │
  │  analytics ─► report  │
  │  report ─► GH issue   │
  └───────────────────────┘
```

## Non-Goals

- Building a custom frontend consuming Ghost Content API (Handlebars theme is sufficient for now)
- Paid membership / monetization setup (structure only, no payment processing)
- LinkedIn adapter (templates exist but no API integration — stays planned)
- Instagram automation (stays manual, visual curation is inherently human)

## Risks

- **Ghost API rate limits** — Mitigated by existing circuit breaker + rate limiter
- **Cross-org dispatch permissions** — Requires `GITHUB_TOKEN` with dispatch permissions; may need a PAT stored as org secret
- **ActivityPub propagation delay** — Federation is async; content may take minutes to appear on Mastodon followers' timelines
- **Ghost theme complexity** — Handlebars templating is limited; keep theme simple, iterate later
