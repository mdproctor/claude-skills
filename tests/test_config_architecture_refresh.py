"""
Tests for the config-architecture.md daily refresh logic in update-claude-md.

The logic under test (extracted from the SKILL.md Step 0 bash script):
  - File missing → fetch and write
  - File < 24h old → skip (no network call)
  - File >= 24h old → fetch and overwrite
  - Fetch fails (empty response / timeout) → keep existing, warn
"""

import os
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


GITHUB_URL = "https://raw.githubusercontent.com/mdproctor/cc-praxis/main/docs/config-architecture.md"
FRESH_CONTENT = "# Claude Configuration Architecture\n\n> **Source:** " + GITHUB_URL
STALE_CONTENT = "# Claude Configuration Architecture\n\n> OLD VERSION"


def needs_update(config_file: Path) -> bool:
    """Mirrors the bash logic: missing or >= 24h old → True."""
    if not config_file.exists():
        return True
    age = time.time() - config_file.stat().st_mtime
    return age >= 86400


def refresh_config_architecture(config_file: Path, fetched_content: str | None) -> tuple[bool, str]:
    """
    Mirrors the bash refresh logic.
    Returns (updated: bool, message: str).
    """
    if fetched_content:
        config_file.write_text(fetched_content)
        return True, "✅ config-architecture.md refreshed"
    else:
        return False, "⚠️  Could not fetch config-architecture.md — keeping existing copy"


# ── needs_update tests ──────────────────────────────────────────────────────

class TestNeedsUpdate:
    def test_missing_file_needs_update(self, tmp_path):
        config_file = tmp_path / "config-architecture.md"
        assert needs_update(config_file) is True

    def test_fresh_file_does_not_need_update(self, tmp_path):
        config_file = tmp_path / "config-architecture.md"
        config_file.write_text(STALE_CONTENT)
        # mtime is now — definitely < 24h
        assert needs_update(config_file) is False

    def test_file_exactly_24h_old_needs_update(self, tmp_path):
        config_file = tmp_path / "config-architecture.md"
        config_file.write_text(STALE_CONTENT)
        old_time = time.time() - 86400
        os.utime(config_file, (old_time, old_time))
        assert needs_update(config_file) is True

    def test_file_older_than_24h_needs_update(self, tmp_path):
        config_file = tmp_path / "config-architecture.md"
        config_file.write_text(STALE_CONTENT)
        old_time = time.time() - (86400 * 3)  # 3 days old
        os.utime(config_file, (old_time, old_time))
        assert needs_update(config_file) is True

    def test_file_23h_old_does_not_need_update(self, tmp_path):
        config_file = tmp_path / "config-architecture.md"
        config_file.write_text(STALE_CONTENT)
        recent_time = time.time() - (86400 - 3600)  # 23h old
        os.utime(config_file, (recent_time, recent_time))
        assert needs_update(config_file) is False


# ── refresh_config_architecture tests ───────────────────────────────────────

class TestRefreshConfigArchitecture:
    def test_successful_fetch_writes_file(self, tmp_path):
        config_file = tmp_path / "config-architecture.md"
        updated, msg = refresh_config_architecture(config_file, FRESH_CONTENT)
        assert updated is True
        assert config_file.read_text() == FRESH_CONTENT
        assert "refreshed" in msg

    def test_successful_fetch_overwrites_stale_file(self, tmp_path):
        config_file = tmp_path / "config-architecture.md"
        config_file.write_text(STALE_CONTENT)
        updated, msg = refresh_config_architecture(config_file, FRESH_CONTENT)
        assert updated is True
        assert config_file.read_text() == FRESH_CONTENT

    def test_failed_fetch_keeps_existing_file(self, tmp_path):
        config_file = tmp_path / "config-architecture.md"
        config_file.write_text(STALE_CONTENT)
        updated, msg = refresh_config_architecture(config_file, None)
        assert updated is False
        assert config_file.read_text() == STALE_CONTENT
        assert "keeping existing" in msg

    def test_failed_fetch_with_no_existing_file(self, tmp_path):
        config_file = tmp_path / "config-architecture.md"
        updated, msg = refresh_config_architecture(config_file, None)
        assert updated is False
        assert not config_file.exists()
        assert "keeping existing" in msg

    def test_empty_string_treated_as_fetch_failure(self, tmp_path):
        config_file = tmp_path / "config-architecture.md"
        config_file.write_text(STALE_CONTENT)
        updated, msg = refresh_config_architecture(config_file, "")
        assert updated is False
        assert config_file.read_text() == STALE_CONTENT


# ── integration: full flow ───────────────────────────────────────────────────

class TestFullRefreshFlow:
    def test_missing_file_fetches_and_writes(self, tmp_path):
        config_file = tmp_path / "config-architecture.md"
        assert needs_update(config_file)
        updated, _ = refresh_config_architecture(config_file, FRESH_CONTENT)
        assert updated
        assert config_file.exists()

    def test_fresh_file_skips_entirely(self, tmp_path):
        config_file = tmp_path / "config-architecture.md"
        config_file.write_text(STALE_CONTENT)
        # File is fresh — should not update
        assert not needs_update(config_file)
        # No fetch needed — content unchanged
        assert config_file.read_text() == STALE_CONTENT

    def test_stale_file_fetches_and_overwrites(self, tmp_path):
        config_file = tmp_path / "config-architecture.md"
        config_file.write_text(STALE_CONTENT)
        old_time = time.time() - (86400 * 2)
        os.utime(config_file, (old_time, old_time))
        assert needs_update(config_file)
        updated, _ = refresh_config_architecture(config_file, FRESH_CONTENT)
        assert updated
        assert config_file.read_text() == FRESH_CONTENT

    def test_stale_file_fetch_failure_preserves_existing(self, tmp_path):
        config_file = tmp_path / "config-architecture.md"
        config_file.write_text(STALE_CONTENT)
        old_time = time.time() - (86400 * 2)
        os.utime(config_file, (old_time, old_time))
        assert needs_update(config_file)
        updated, msg = refresh_config_architecture(config_file, None)
        assert not updated
        assert config_file.read_text() == STALE_CONTENT
        assert "keeping existing" in msg
