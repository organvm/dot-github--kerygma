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

## 8. Verification Checklist

After the first dispatch, verify:

- [ ] Mastodon: Post visible on your profile
- [ ] Discord: Embed appears in the configured channel
- [ ] Bluesky: Post visible on your profile
- [ ] Ghost: Draft or published post appears in admin
- [ ] GitHub: Distribution report issue created in `.github` repo
- [ ] Status badge: Updated from "0 dispatches" to "1 dispatch"
- [ ] Delivery log: Entry recorded in `docs/dispatch-log.md`

---

## 9. Ongoing Operations

### Automated Workflows (cron)

| Workflow | Schedule | Action |
|----------|----------|--------|
| `rss-auto-dispatch.yml` | Every 6 hours | Polls ORGAN-V Atom feed for new essays |
| `weekly-analytics.yml` | Monday 09:00 UTC | Creates weekly report GitHub issue |

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
- **Weekly reports**: Auto-created as GitHub issues every Monday
- **Delivery log**: JSON file tracking all syndication records for deduplication

### Troubleshooting

| Symptom | Check |
|---------|-------|
| Dispatch silently skipped | `delivery_log.json` — may be deduplication |
| Template not found | `python kerygma_pipeline.py templates` — verify template ID |
| Platform timeout | `python .github/scripts/validate-live-config.py` — check connectivity |
| Quality check failure | Preview the template and check character limits |
| Circuit breaker open | Wait for reset timeout (default 60s), or check platform status |

---

*Generated as part of the VIVIFICATIO sprint. Last updated: 2026-02-24.*
