# Kerygma Operational Runbook

Step-by-step guide to configuring and operating the ORGAN-VII distribution pipeline.

---

## 1. Ghost Instance Setup

### Option A: Ghost(Pro)
1. Sign up at [ghost.org](https://ghost.org)
2. Create a new site (recommended subdomain: `newsletter.yourdomain.com`)
3. Note the admin URL (e.g., `https://newsletter.yourdomain.com`)

### Option B: Self-Hosted
1. Follow [Ghost self-hosting guide](https://ghost.org/docs/install/)
2. Configure with a reverse proxy (nginx/Caddy)
3. Enable HTTPS

### Post-Setup
- Create a Custom Integration under Settings > Integrations
- Copy the **Admin API Key** (format: `{id}:{secret}`)
- Note the **API URL** (your site URL)

---

## 2. Ghost Theme Deployment

Deploy the custom `organvm-theme/` (newsletter CTA, reading progress bar, related posts, mobile hamburger menu):

```bash
cd .github
python scripts/deploy-ghost-theme.py
```

Required env vars:
- `KERYGMA_GHOST_API_URL` — Ghost site URL
- `KERYGMA_GHOST_ADMIN_API_KEY` — Admin API key from step 1

The script zips `organvm-theme/` and uploads via Ghost Admin API.

---

## 3. Mastodon Account Setup

1. Register an account on your preferred Mastodon instance (e.g., mastodon.social, hachyderm.io)
2. Go to Preferences > Development > New Application
3. Configure:
   - Application name: `kerygma-pipeline`
   - Scopes: `read`, `write:statuses`
4. Copy the **Access Token**
5. Note the **Instance URL** (e.g., `https://mastodon.social`)

---

## 4. Discord Server + Webhook

1. Create or select a Discord server
2. Go to Server Settings > Integrations > Webhooks
3. Create a new webhook:
   - Name: `Kerygma Pipeline`
   - Channel: Select the announcements channel
4. Copy the **Webhook URL**

---

## 5. Bluesky Account Setup

1. Create an account at [bsky.app](https://bsky.app) (or use existing)
2. Go to Settings > App Passwords
3. Generate a new app password (name: `kerygma-pipeline`)
4. Note your **Handle** (e.g., `yourname.bsky.social`)
5. Copy the **App Password**

---

## 6. GitHub Secrets Configuration

Configure these secrets in the `.github` repo (Settings > Secrets > Actions):

| Secret Name | Source | Format |
|-------------|--------|--------|
| `KERYGMA_MASTODON_ACCESS_TOKEN` | Step 3 | Bearer token string |
| `KERYGMA_DISCORD_WEBHOOK_URL` | Step 4 | Full webhook URL |
| `KERYGMA_BLUESKY_HANDLE` | Step 5 | `yourname.bsky.social` |
| `KERYGMA_BLUESKY_APP_PASSWORD` | Step 5 | App password string |
| `KERYGMA_GHOST_API_URL` | Step 1 | `https://newsletter.yourdomain.com` |
| `KERYGMA_GHOST_ADMIN_API_KEY` | Step 1 | `{id}:{secret}` format |

For cross-organ triggers, also set `CROSS_ORG_DISPATCH_TOKEN` (a GitHub PAT with `repo` scope) in the source organ repos.

---

## 7. First-Fire Procedure

### Pre-flight (dry-run)
```bash
# Set env vars locally for testing
export KERYGMA_GHOST_API_URL="https://your-ghost-site.com"
export KERYGMA_GHOST_ADMIN_API_KEY="your-id:your-secret"
export KERYGMA_MASTODON_INSTANCE_URL="https://mastodon.social"
export KERYGMA_MASTODON_ACCESS_TOKEN="your-token"
export KERYGMA_DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
export KERYGMA_BLUESKY_HANDLE="your.bsky.social"
export KERYGMA_BLUESKY_APP_PASSWORD="your-app-password"

# Run pre-flight checks
python .github/scripts/first-fire.py
```

### Live dispatch
```bash
# Only after all pre-flight checks pass:
python .github/scripts/first-fire.py --live
```

---

## 8. Scheduling

The pipeline includes a calendar-aware content scheduler (added in NEXUS PERPETUUS).

### List scheduled entries
```bash
python kerygma-pipeline/kerygma_pipeline.py schedule list
```

### Add a scheduled entry
```bash
python kerygma-pipeline/kerygma_pipeline.py schedule add \
  --content-id essay-announce \
  --channels mastodon,discord \
  --at 2026-03-01T10:00:00 \
  --frequency once
```

### Show entries due now (with priority scores)
```bash
python kerygma-pipeline/kerygma_pipeline.py schedule due
```

### Process all due entries
```bash
python kerygma-pipeline/kerygma_pipeline.py schedule process
```

This renders, quality-checks, dispatches, and records analytics for each due entry, respecting calendar modifiers.

---

## 9. Backfill

Scan a Jekyll `_posts/` directory and schedule undistributed posts for distribution.

### Dry-run (preview what would be scheduled)
```bash
python kerygma-pipeline/kerygma_pipeline.py backfill \
  --posts-dir ~/Workspace/organvm-v-logos/public-process/_posts \
  --channels mastodon,discord \
  --stagger 30
```

### Execute (create actual schedule entries)
```bash
python kerygma-pipeline/kerygma_pipeline.py backfill \
  --posts-dir ~/Workspace/organvm-v-logos/public-process/_posts \
  --channels mastodon,discord \
  --stagger 30 \
  --execute
```

Options:
- `--stagger N` — minutes between staggered posts (default: 30)
- `--channels` — comma-separated target channels
- `--execute` — actually create entries (without this flag, it's a dry-run)

---

## 10. Verification Checklist

After the first dispatch, verify:

- [ ] Mastodon: Post visible on your profile
- [ ] Discord: Embed appears in the configured channel
- [ ] Bluesky: Post visible on your profile
- [ ] Ghost: Draft or published post appears in admin
- [ ] GitHub: Distribution report issue created in `.github` repo
- [ ] Status badge: Updated from "0 dispatches" to "1 dispatch"
- [ ] Delivery log: Entry recorded in `docs/dispatch-log.md`
- [ ] Scheduler: `schedule list` shows no stale entries
- [ ] Calendar: Events loaded (check via `status` command)

---

## 11. Ongoing Operations

### Automated Workflows (cron)

| Workflow | Schedule | Action |
|----------|----------|--------|
| `rss-auto-dispatch.yml` | Every 6 hours | Polls ORGAN-V Atom feed, processes via scheduler |
| `weekly-analytics.yml` | Monday 09:00 UTC | Creates weekly report GitHub issue (ReportGenerator format) |
| `quarterly-feedback.yml` | 1st Monday of Q1/Q2/Q3/Q4 | Collects quarterly signals for Edge 6 synthesis |

### Manual Operations

**Trigger a dispatch manually:**
```bash
python kerygma-pipeline/kerygma_pipeline.py dispatch \
  --template essay-announce \
  --repo public-process \
  --channels mastodon,discord,bluesky,ghost
```

**Preview a template without dispatching:**
```bash
python kerygma-pipeline/kerygma_pipeline.py preview \
  --template essay-announce \
  --repo public-process \
  --channel mastodon
```

**Generate a distribution report:**
```bash
python kerygma-pipeline/kerygma_pipeline.py report --period weekly
```

**Check pipeline health:**
```bash
python kerygma-pipeline/kerygma_pipeline.py status
python kerygma-pipeline/kerygma_pipeline.py activate
```

### Monitoring

- **Status badge**: Shields.io endpoint at `docs/status-badge.json`, auto-updated after each dispatch
- **Dispatch log**: `docs/dispatch-log.md` records all dispatch attempts
- **Weekly reports**: Auto-created as GitHub issues every Monday (ReportGenerator format with schedule + calendar sections)
- **Delivery log**: JSON file tracking all syndication records for deduplication

### Troubleshooting

| Symptom | Check |
|---------|-------|
| Dispatch silently skipped | `delivery_log.json` — may be deduplication |
| Template not found | `python kerygma_pipeline.py templates` — verify template ID |
| Platform timeout | `python .github/scripts/validate-live-config.py` — check connectivity |
| Quality check failure | Preview the template and check character limits |
| Circuit breaker open | Wait for reset timeout (default 60s), or check platform status |
| Scheduler entries stuck | `schedule list` then `schedule process` — check for errors |
| Calendar not loading | Verify `calendar:` section in `kerygma_config.yaml` |

---

---

## 12. Per-Project Social Identity

The IDENTITAS PERPETUA system enables per-project social accounts, voice, and distribution. Each project can have its own Mastodon handle, Discord webhook, tone, and hashtags.

### Profile Onboarding Checklist

1. Create a new YAML file in `kerygma-profiles/profiles/<project-id>.yaml`
2. Set `profile_id`, `display_name`, `organ`, and `repos` (list of repo names this profile handles)
3. Configure `voice` — `tone`, `hashtags`, `tagline`
4. Add platform credentials using `op://` references (e.g., `op://kerygma/<project>-mastodon/access-token`)
5. Define `channels` with `channel_id`, `platform`, `max_length`, `enabled`
6. Run `kerygma-profiles validate <project-id>` to verify secrets resolve
7. Test with `python kerygma-pipeline/kerygma_pipeline.py preview --template essay-announce --repo <repo-name> --channel mastodon`

### 1Password Setup for CI

For GitHub Actions to resolve `op://` secrets:
1. Create a 1Password Service Account with access to the `kerygma` vault
2. Set `OP_SERVICE_ACCOUNT_TOKEN` as a GitHub Actions secret
3. Install `op` CLI in the workflow (use `1password/install-cli-action@v1`)
4. Secrets are resolved automatically by `kerygma_profiles.secrets.resolve_secret()`

Alternatively, use `KERYGMA_PROFILE_*` env var fallbacks:
- `op://kerygma/mastodon-system/access-token` → `KERYGMA_PROFILE_MASTODON_SYSTEM_ACCESS_TOKEN`

### Profile YAML Reference

```yaml
profile_id: my-product          # unique identifier
display_name: "My Product"      # human-readable name
organ: III                       # organ number (or null for system-wide)
repos:                           # repos this profile handles
  - my-product-api
  - my-product-docs

voice:
  tone: friendly                 # friendly, institutional, technical, etc.
  hashtags: ["#myproduct", "#saas"]
  tagline: "Build better with My Product"

platforms:
  mastodon:
    instance_url: "https://mastodon.social"
    access_token: "op://kerygma/my-product-mastodon/access-token"
    visibility: public
  discord:
    webhook_url: "op://kerygma/my-product-discord/webhook-url"

channels:
  - channel_id: mastodon-product
    platform: mastodon
    max_length: 500
    enabled: true

calendar:
  events: []

rss_feed_url: ""
```

### CLI Commands

```bash
# List all profiles
kerygma-profiles list

# Show a profile (secrets redacted)
kerygma-profiles show my-product

# Validate all profiles (checks secret resolution)
kerygma-profiles validate

# Validate one profile
kerygma-profiles validate my-product

# Pipeline with profiles
python kerygma-pipeline/kerygma_pipeline.py --profiles-dir kerygma-profiles/profiles status
python kerygma-pipeline/kerygma_pipeline.py --profiles-dir kerygma-profiles/profiles profiles list
python kerygma-pipeline/kerygma_pipeline.py --profiles-dir kerygma-profiles/profiles dispatch \
  --template essay-announce --repo my-product-api --channels mastodon --profile my-product
```

---

*Generated as part of the IDENTITAS PERPETUA sprint. Last updated: 2026-02-24.*
