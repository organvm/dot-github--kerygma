# ORGAN-VII (Kerygma) — Evaluation-to-Growth Review

**Date:** 2026-02-24  
**Scope:** Full system review — `announcement-templates`, `social-automation`, `distribution-strategy`, `kerygma-pipeline`  
**Methodology:** 9-phase Evaluation-to-Growth (E2G) framework  
**Reviewer:** AI-assisted analysis (Claude Code)

---

## Phase 1: Critique

### 1.1 Strengths

- **Clean three-package architecture**: Templates, social automation, and distribution strategy are well-decomposed into independently installable packages, with `kerygma-pipeline` as a thin orchestrator wiring them together.
- **Zero external dependencies** in `announcement-templates` — the template engine uses regex-based parsing (no Jinja2, no pyyaml), signaling deliberate craftsmanship.
- **Resilience stack is textbook**: Rate limiter (outermost) → circuit breaker (fail-fast) → retry with exponential backoff (innermost), each in its own module (`rate_limiter.py`, `circuit_breaker.py`, `retry.py`). See `PosseDistributor._with_resilience()`.
- **Dry-run by default** across all platform clients (`live=False`). Safe experimentation is the default; live mode requires explicit opt-in via config or env var.
- **Delivery deduplication** via `DeliveryLog.has_been_delivered()` prevents double-posting — `PosseDistributor.syndicate()` checks before dispatching.
- **Atomic writes everywhere**: `JsonStore`, `DeliveryLog`, and `RssPoller` all use `os.replace()` via temp files.
- **Comprehensive test suite**: 30 test files across 4 packages with per-module coverage, integration tests, and fixture patterns.
- **Zero TODOs/FIXMEs** in the codebase — unusual maturity signal for a system this size.
- **Consistent patterns**: Every client follows the `live=False` mock pattern; every store uses atomic writes; every CLI uses argparse with subcommands.
- **16 well-structured templates** across 5 categories (`launch/`, `release/`, `essay/`, `community/`, `institutional/`) with 5-channel coverage each.

### 1.2 Weaknesses

| ID | Severity | Location | Description |
|----|----------|----------|-------------|
| W1 | Medium | `ghost.py:48-80`, `ghost_metrics.py:32-47` | Duplicated Ghost JWT builder (~30 lines each, near-identical logic) |
| W2 | Medium | `cli.py:25-57`, `kerygma_pipeline.py:110-150` | Duplicated `_build_distributor` factory (structurally identical) |
| W3 | Low | All three `__init__.py` | Empty `__init__.py` files — no public API surface for consumers |
| W4 | Info | `posse.py:70` | `ContentPost.created_at` uses `default_factory=datetime.now` — correct but looks like a common pitfall |
| W5 | High | `kerygma_pipeline.py:308` | RSS poller created without `seen_path`, losing dedup state between invocations |
| W6 | Info | Superproject CLAUDE.md | `announcement-templates` marked as tier `archive` in seed.yaml but actively used |
| W7 | Info | seed.yaml files | `promotion_status` says LOCAL but CLAUDE.md says GRADUATED |
| W8 | Low | `.github/.github/workflows/ci-pipeline.yml` | Path filter only triggers on `kerygma_pipeline.py` and `tests/**`, missing 3 submodule packages |

---

## Phase 2: Reinforcement

Areas requiring structural improvement, addressed in the implementation plan:

1. **Ghost JWT consolidation** (W1) → Extract to shared utility, import from both `ghost.py` and `ghost_metrics.py`
2. **Distributor factory consolidation** (W2) → Move to `kerygma_social.factory` module
3. **RSS poller statefulness** (W5) → Pass `seen_path` derived from delivery log path

---

## Phase 3: Logic Check

### Template Engine Conditional Nesting
The regex-based conditional parser in `engine.py` uses repeated `re.sub()` for nested `{{#if}}` blocks. Sound at current scale (templates are < 100 lines each, max 2-3 nesting levels). Performance would degrade with deep nesting (O(n²) regex passes), but this is a theoretical concern — not actionable.

### Resilience Layer Interaction
`_with_resilience()` composes `cb.call(retry, _retryable, config)` — the circuit breaker wraps the retry function, meaning:
- If the circuit is OPEN, `CircuitOpenError` propagates immediately (correct — not retried)
- If CLOSED/HALF_OPEN, the retry function handles transient failures within the circuit breaker call
- A retry exhaustion (`RetryError`) counts as a single circuit breaker failure

This is **intentional and correct**, but the indirection is non-obvious. A code comment documents it well.

### Scheduler Recurring Entry IDs
`publish_entry()` creates `{entry_id}-next` for recurring entries. If the same recurring entry fires twice (publish → auto-create → publish → auto-create), the second `-next` ID would collide with the first. The `schedule()` method's uniqueness check would raise `ValueError`. **This is a bug** — addressed in P0.4.

### RSS Feed Parsing
`parse_feed()` handles both Atom and RSS 2.0 by checking for `{ATOM_NS}entry` elements first. Correct and handles edge cases (missing `link@rel=alternate`, missing `guid`).

---

## Phase 4: Logos (Rational Appeal)

The architecture faithfully implements the POSSE pattern:

- **17 event types** map to **13 unique templates** via `EVENT_TEMPLATE_MAP`
- **4 platforms automated**: Mastodon, Discord, Bluesky, Ghost
- **2 platforms manual**: Twitter, LinkedIn — wise decision given API volatility and cost
- **Config cascade** (YAML → env vars) is clean: `_env_or()` and `_env_bool()` helpers, `KERYGMA_` prefix
- **Pipeline flow** is linear and traceable: event → template → render → quality check → dispatch → analytics
- **Registry integration** pulls from ORGAN-IV's `registry.json` for template variable interpolation

The system does exactly what it claims with no hidden complexity.

---

## Phase 5: Pathos (Emotional Resonance)

### Template Tone
Templates are professional but generic:
- "Excited to announce" (LinkedIn channel blocks)
- "New essay published" (Mastodon channel blocks)
- No platform-native voice differentiation

### Platform Affordances Underutilized
- **Discord**: `DiscordEmbed` constructs embeds with fields, but templates produce plain text that gets wrapped in a basic embed. Rich field layouts are available but unused.
- **Bluesky**: AT Protocol supports facets/rich text links. The client formats text but doesn't construct facets.
- **Mastodon**: `split_for_thread()` exists but is never called from the pipeline — long-form essay distribution could use threads.

### Opportunity
Templates could benefit from per-platform voice guidelines (e.g., casual on Mastodon, professional on Ghost, community-forward on Discord).

---

## Phase 6: Ethos (Credibility)

### Trust Signals
- Zero-dependency template engine signals craftsmanship
- Comprehensive test suite builds confidence
- Atomic writes show production awareness
- `live_mode: false` default is responsible engineering
- Consistent patterns across all modules

### Gaps
- No `py.typed` marker for type-checker consumers
- No `LICENSE` in individual packages (only in `.github`)
- No structured logging (all output is `print()`)

---

## Phase 7: Risk Analysis

### 7.1 Blind Spots

| Risk | Severity | Description |
|------|----------|-------------|
| R1 | Medium | No timeout on circuit breaker in HALF_OPEN state — if the trial request hangs, circuit stays HALF_OPEN indefinitely |
| R2 | Medium | No max log size — `DeliveryLog` and `RssPoller` seen_ids grow unbounded over months of operation |
| R3 | Medium | No retry differentiation — all exceptions trigger retry, including `ValueError` and `CircuitOpenError` |
| R4 | Low | Ghost JWT is rebuilt per-request (correct but undocumented as intentional design choice) |
| R5 | Medium | No structured logging — `print()` output is unparseable in CI and production |
| R6 | Info | `announcement-templates` tier is `archive` in seed.yaml but it's actively used by the pipeline |

### 7.2 Shatter Points

| ID | Severity | Location | Description |
|----|----------|----------|-------------|
| S1 | Critical | `kerygma_pipeline.py:44` | `TEMPLATES_DIR` is hardcoded relative to `__file__` — assumes superproject layout. Works in CI only because tests run from the superproject checkout. |
| S2 | Critical | `kerygma_pipeline.py:308` | RSS poller dedup state lost between pipeline invocations. Cron-triggered `rss-auto-dispatch.yml` could re-dispatch old essays. |
| S3 | Medium | `discord.py:25` | `DiscordEmbed.add_field()` stores `inline` as `str("true"/"false")` — Discord API expects boolean JSON. Live mode embeds will always have `inline: false`. |
| S4 | Medium | `mastodon.py:33` | `Toot.validate()` hardcodes 500 char limit, ignoring `MastodonConfig.max_chars`. Instances with different limits would silently truncate or fail validation. |

---

## Phase 8: Growth

### 8.1 Bloom (Untapped Potential)

- **Thread support**: `MastodonClient.split_for_thread()` exists but is unused in the pipeline. Could enable long-form essay distribution as Mastodon threads.
- **Engagement feedback loop**: Metrics adapters (`ghost_metrics.py`, `mastodon_metrics.py`) exist but aren't wired into the pipeline. Could inform scheduling priority.
- **Template inheritance**: The engine could support base templates with channel-specific overrides, reducing template count.
- **Webhook receivers**: `dispatch-receiver.yml` could be generalized to accept events from any organ via a standardized payload schema.

### 8.2 Evolve (Implementation Items)

See the implementation section below. Items are prioritized P0 (bugs) through P3 (polish).

---

## Phase 9: Synthesis

ORGAN-VII is a **mature, well-architected** POSSE distribution system. Its strengths — clean decomposition, resilience engineering, safety-by-default — significantly outweigh its weaknesses.

**Critical issues** (P0) are limited to:
1. RSS dedup state loss risking duplicate dispatches
2. Discord embed inline type mismatch
3. Mastodon validation ignoring instance-specific char limits
4. Scheduler recurring ID collisions

**Structural improvements** (P1) are DRY consolidations that reduce maintenance surface without changing behavior.

**Resilience hardening** (P2) addresses unbounded growth and indiscriminate retry — both are time-bombs that would manifest in production.

**Overall maturity**: The system is GRADUATED-ready. All 4 submodules have comprehensive tests, consistent patterns, and responsible defaults. The zero-TODO codebase is a strong signal.

---

## Implementation Summary

| Priority | Count | Items |
|----------|-------|-------|
| P0 (Bugs) | 4 | RSS dedup, Discord inline, Toot validate, scheduler IDs |
| P1 (DRY) | 2 | Ghost JWT, distributor factory |
| P2 (Resilience) | 2 | Retry filtering, log rotation |
| P3 (Polish) | 1 | `__init__.py` exports |

Total: **9 implementation items** across **12 files modified**, **1 file created** (this report).

---

*Generated by Evaluation-to-Growth framework — ORGAN-VII system review, February 2026*
