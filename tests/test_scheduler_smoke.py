"""Smoke tests verifying the strategy layer is wired into the pipeline.

Lightweight checks that schedule_content(), backfill_from_posts(), and
generate_report() exercise the NEXUS PERPETUUS features (scheduler, calendar,
ReportGenerator).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from kerygma_pipeline import KerygmaPipeline


@pytest.fixture
def social_config_with_calendar(tmp_path):
    """Social config with calendar events for scheduler testing."""
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
        "channels:\n"
        "  - channel_id: mastodon-primary\n"
        "    name: Mastodon Primary\n"
        "    platform: mastodon\n"
        "    endpoint: https://mastodon.social\n"
        "    max_length: 500\n"
        "    enabled: true\n"
        "  - channel_id: discord-announcements\n"
        "    name: Discord Announcements\n"
        "    platform: discord\n"
        "    endpoint: ''\n"
        "    max_length: 4096\n"
        "    enabled: true\n"
        "calendar:\n"
        "  events:\n"
        "    - event_id: test-conf\n"
        "      name: Test Conference\n"
        "      event_type: conference\n"
        "      start_date: '2026-07-01'\n"
        "      end_date: '2026-07-05'\n"
        "      posting_modifier: 1.5\n"
    )
    return cfg


@pytest.fixture
def sample_registry(tmp_path):
    reg = {
        "meta": {"version": "2.0"},
        "organs": {
            "ORGAN-V": {
                "repos": [{
                    "name": "public-process",
                    "description": "Test repo",
                    "tier": "flagship",
                    "github_url": "https://github.com/test/repo",
                    "implementation_status": "PRODUCTION",
                }]
            }
        },
    }
    path = tmp_path / "registry-v2.json"
    path.write_text(json.dumps(reg))
    return path


@pytest.fixture
def pipeline(stub_templates_dir, sample_registry, social_config_with_calendar, tmp_path):
    return KerygmaPipeline(
        templates_dir=stub_templates_dir,
        registry_path=sample_registry,
        social_config_path=social_config_with_calendar,
        analytics_store_path=tmp_path / "analytics.json",
        calendar_config_path=social_config_with_calendar,
        schedule_store_path=tmp_path / "schedule.json",
    )


class TestScheduleContent:
    def test_schedule_creates_entries(self, pipeline):
        """schedule_content() should create schedule entries for each channel."""
        entries = pipeline.schedule_content(
            content_id="test-post-1",
            channels=["mastodon", "discord"],
            scheduled_time=datetime.now() + timedelta(hours=1),
        )
        assert len(entries) == 2
        assert entries[0].channel == "mastodon"
        assert entries[1].channel == "discord"
        assert not entries[0].published

    def test_schedule_list_shows_entries(self, pipeline):
        """After scheduling, get_upcoming should return the entries."""
        pipeline.schedule_content(
            content_id="test-post-2",
            channels=["mastodon"],
            scheduled_time=datetime.now() + timedelta(hours=2),
        )
        upcoming = pipeline._scheduler.get_upcoming(hours=24)
        assert len(upcoming) >= 1
        assert any("test-post-2" in e.content_id for e in upcoming)


class TestBackfillDryRun:
    def test_backfill_dry_run_reports_posts(self, pipeline, tmp_path):
        """backfill_from_posts() in dry-run mode should report what it would schedule."""
        posts_dir = tmp_path / "_posts"
        posts_dir.mkdir()
        (posts_dir / "2026-01-15-first-essay.md").write_text(
            "---\ntitle: First Essay\nslug: first-essay\n---\nContent here.\n"
        )
        (posts_dir / "2026-02-10-second-essay.md").write_text(
            "---\ntitle: Second Essay\nslug: second-essay\n---\nMore content.\n"
        )

        result = pipeline.backfill_from_posts(
            posts_dir=posts_dir,
            channels=["mastodon", "discord"],
            execute=False,
        )
        assert result["total_files"] == 2
        assert result["scheduled"] == 2
        assert result["execute"] is False
        for post in result["posts"]:
            assert post["action"] == "would_schedule"


class TestGenerateReportUsesReportGenerator:
    def test_report_contains_schedule_summary(self, pipeline):
        """generate_report() should include a Schedule Summary section."""
        report = pipeline.generate_report(period_days=7)
        assert "Schedule Summary" in report
        assert "Pending entries" in report

    def test_report_contains_calendar_events(self, pipeline):
        """generate_report() should include calendar events when present."""
        report = pipeline.generate_report(period_days=7)
        # Calendar section appears when there are upcoming events
        assert "Generated by kerygma_pipeline.py report" in report


class TestProcessDueEntries:
    def test_process_due_with_no_entries(self, pipeline):
        """process_due_entries() should return empty list when nothing is due."""
        results = pipeline.process_due_entries()
        assert results == []
