"""Tests for live config validator — mock all HTTP calls."""
import types
from unittest.mock import patch, MagicMock

import pytest


def _import_validator():
    """Import the script as a module."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "validate_live_config",
        "scripts/validate-live-config.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestCheckEndpoint:
    def test_success_returns_true(self):
        mod = _import_validator()
        with patch("urllib.request.urlopen") as mock_open:
            mock_resp = MagicMock()
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_resp.status = 200
            mock_open.return_value = mock_resp
            assert mod.check_endpoint("Ghost", "https://example.com/ghost/api/admin/site/", {}) is True

    def test_failure_returns_false(self):
        mod = _import_validator()
        with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
            assert mod.check_endpoint("Ghost", "https://bad.example.com", {}) is False


class TestBuildChecks:
    def test_ghost_check_skipped_without_env(self):
        mod = _import_validator()
        with patch.dict("os.environ", {}, clear=True):
            checks = mod.build_checks()
            ghost_checks = [c for c in checks if c[0] == "Ghost"]
            assert len(ghost_checks) == 0

    def test_ghost_check_present_with_env(self):
        mod = _import_validator()
        env = {
            "KERYGMA_GHOST_API_URL": "https://ghost.example.com",
            "KERYGMA_GHOST_ADMIN_API_KEY": "abc123:deadbeef0102030405060708090a0b0c0d0e0f101112131415161718191a1b",  # allow-secret — test fixture
        }
        with patch.dict("os.environ", env, clear=True):
            checks = mod.build_checks()
            ghost_checks = [c for c in checks if c[0] == "Ghost"]
            assert len(ghost_checks) == 1
