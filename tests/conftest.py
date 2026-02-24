"""Shared fixtures for pipeline integration tests.

Creates minimal template stubs so tests are self-contained and do not
depend on the announcement-templates submodule being checked out at a
particular relative path.
"""

from __future__ import annotations

from pathlib import Path

import pytest


# Every unique template_id referenced by EVENT_TEMPLATE_MAP in kerygma_pipeline.py.
# Each entry: (template_id, category, channels list)
_TEMPLATE_STUBS: list[tuple[str, str, list[str]]] = [
    ("essay-announce", "essay", ["mastodon", "discord", "bluesky", "ghost"]),
    ("feature-release", "release", ["mastodon", "discord", "bluesky", "ghost"]),
    ("repo-launch", "launch", ["mastodon", "discord", "bluesky", "ghost"]),
    ("salon-invite", "community", ["mastodon", "discord", "ghost"]),
    ("bugfix-release", "release", ["mastodon", "discord"]),
    ("system-milestone", "launch", ["mastodon", "discord", "ghost"]),
    ("workshop-sprint", "community", ["mastodon", "discord", "ghost"]),
    ("partnership", "institutional", ["mastodon", "discord", "ghost"]),
    ("press-release", "institutional", ["mastodon", "discord", "ghost"]),
    ("grant-supplement", "institutional", ["mastodon", "discord", "ghost"]),
    ("organ-launch", "launch", ["mastodon", "discord", "bluesky", "ghost"]),
    ("breaking-change", "release", ["mastodon", "discord", "ghost"]),
    ("community-milestone", "community", ["mastodon", "discord", "ghost"]),
    ("reading-group", "community", ["mastodon", "discord"]),
    ("essay-highlight", "essay", ["mastodon", "discord", "ghost"]),
    ("essay-series", "essay", ["mastodon", "discord", "bluesky", "ghost"]),
]


def _make_stub_template(template_id: str, category: str, channels: list[str]) -> str:
    """Generate a minimal .md template with frontmatter and channel blocks."""
    channels_inline = ", ".join(channels)
    blocks = []
    for ch in channels:
        blocks.append(
            f"{{{{#channel {ch}}}}}\n"
            f"[{template_id}] {{{{ event.title }}}} — {{{{ event.summary }}}} "
            f"https://example.com/{{{{ repo.name }}}}\n"
            f"{{{{/channel}}}}"
        )
    body = "\n\n".join(blocks)
    return (
        f"---\n"
        f"template_id: {template_id}\n"
        f"category: {category}\n"
        f"channels: [{channels_inline}]\n"
        f"variables: [event.title, event.summary, repo.name]\n"
        f"---\n\n"
        f"{body}\n"
    )


@pytest.fixture()
def stub_templates_dir(tmp_path: Path) -> Path:
    """Create a temporary directory populated with all template stubs."""
    templates_dir = tmp_path / "templates"
    for template_id, category, channels in _TEMPLATE_STUBS:
        category_dir = templates_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        content = _make_stub_template(template_id, category, channels)
        (category_dir / f"{template_id}.md").write_text(content)
    return templates_dir
