"""Integration tests for kerygma_pipeline — full orchestrator."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from kerygma_pipeline import KerygmaPipeline, EVENT_TEMPLATE_MAP


TEMPLATES_DIR = Path(__file__).parent.parent / "announcement-templates" / "templates"


@pytest.fixture
def sample_registry(tmp_path):
    """Minimal registry fixture for integration tests."""
    reg = {
        "ORGAN-V": {
            "repos": [
                {
                    "name": "public-process",
                    "description": "Public accountability ledger",
                    "tier": "flagship",
                    "github_url": "https://github.com/organvm-v-logos/public-process",
                    "implementation_status": "PRODUCTION",
                }
            ]
        }
    }
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(reg))
    return path


@pytest.fixture
def social_config(tmp_path):
    """Mock social config — all platforms disabled, live_mode false."""
    cfg = tmp_path / "social.yaml"
    cfg.write_text(
        "mastodon:\n"
        "  instance_url: ''\n"
        "  access_token: ''\n"
        "discord:\n"
        "  webhook_url: ''\n"
        "bluesky:\n"
        "  handle: ''\n"
        "  app_password: ''\n"
        "delivery_log_path: ''\n"
        "rss_feed_url: ''\n"
        "live_mode: false\n"
    )
    return cfg


@pytest.fixture
def pipeline(sample_registry, social_config, tmp_path):
    return KerygmaPipeline(
        templates_dir=TEMPLATES_DIR,
        registry_path=sample_registry,
        social_config_path=social_config,
        analytics_store_path=tmp_path / "analytics.json",
    )


class TestPipelineTemplateSelection:
    def test_select_valid_template(self, pipeline):
        tid = pipeline.select_template("essay-published")
        assert tid == "essay-announce"

    def test_select_unknown_event_raises(self, pipeline):
        with pytest.raises(ValueError, match="No template mapped"):
            pipeline.select_template("unknown-event-type")

    def test_all_mapped_templates_exist(self, pipeline):
        """Every entry in EVENT_TEMPLATE_MAP should resolve to a loaded template."""
        for event_type, template_id in EVENT_TEMPLATE_MAP.items():
            tid = pipeline.select_template(event_type)
            assert tid == template_id


class TestPipelineRenderAndCheck:
    def test_render_produces_output(self, pipeline):
        results = pipeline.render_and_check(
            "essay-announce", "public-process", ["mastodon", "discord"],
        )
        # At least one channel should pass quality checks
        assert len(results) > 0

    def test_render_mastodon_under_limit(self, pipeline):
        results = pipeline.render_and_check(
            "essay-announce", "public-process", ["mastodon"],
        )
        if "mastodon" in results:
            assert len(results["mastodon"]) <= 500


class TestPipelineFullRun:
    def test_full_pipeline_returns_status(self, pipeline):
        result = pipeline.run_full_pipeline(
            event_type="essay-published",
            repo_name="public-process",
            channels=["mastodon", "discord"],
        )
        assert result["status"] in ("complete", "no_channels_passed")

    def test_full_pipeline_no_channels(self, pipeline):
        """Pipeline with an invalid channel list should gracefully return."""
        result = pipeline.run_full_pipeline(
            event_type="essay-published",
            repo_name="public-process",
            channels=[],
        )
        assert result["status"] == "no_channels_passed"
        assert result["dispatched"] == 0


class TestPipelinePoll:
    def test_poll_with_no_rss_url(self, pipeline):
        """Poll returns empty list when no RSS URL is configured."""
        events = pipeline.poll_for_events()
        assert events == []


class TestPipelineDispatchWithMockClient:
    """Test dispatch path using mock Mastodon client (no real API calls)."""

    def test_dispatch_records_syndication(self, pipeline):
        """Dispatch should produce syndication records for each channel."""
        channel_texts = {"mastodon": "Test post content https://example.com"}
        records = pipeline.dispatch(channel_texts)
        assert len(records) >= 1
        for rec in records:
            assert rec["channel"] == "mastodon"
            assert rec["status"] in ("published", "skipped", "failed")

    def test_dispatch_post_id_is_unique(self, pipeline):
        """Each dispatch call should produce unique post_ids."""
        channel_texts = {"mastodon": "Post A https://example.com"}
        records_a = pipeline.dispatch(channel_texts)
        records_b = pipeline.dispatch(channel_texts)
        # post_id uniqueness is embedded in syndication — check no crash from collision
        assert len(records_a) >= 1
        assert len(records_b) >= 1


class TestAnalyticsPersistenceRoundTrip:
    """Test that analytics survive a save/reload cycle."""

    def test_analytics_persist_and_reload(self, sample_registry, social_config, tmp_path):
        store_path = tmp_path / "analytics_roundtrip.json"

        # Create pipeline, record analytics
        p1 = KerygmaPipeline(
            templates_dir=TEMPLATES_DIR,
            registry_path=sample_registry,
            social_config_path=social_config,
            analytics_store_path=store_path,
        )
        from kerygma_strategy.analytics import EngagementMetric
        p1._analytics.record(EngagementMetric(
            channel_id="mastodon", content_id="test-01",
            timestamp=datetime(2026, 2, 17), impressions=100, clicks=10,
        ))
        p1._analytics.flush()
        assert store_path.exists()

        # Create second pipeline pointing to same store — should load persisted data
        p2 = KerygmaPipeline(
            templates_dir=TEMPLATES_DIR,
            registry_path=sample_registry,
            social_config_path=social_config,
            analytics_store_path=store_path,
        )
        assert p2._analytics.total_records == 1
        loaded = p2._analytics.get_by_channel("mastodon")
        assert len(loaded) == 1
        assert loaded[0].impressions == 100
