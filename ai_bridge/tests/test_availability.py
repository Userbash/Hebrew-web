from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from ai_bridge.core.availability import ModelAvailability, ProviderHealth, ProviderStatus


def test_availability_init() -> None:
    avail = ModelAvailability()
    assert avail is not None


@patch("subprocess.run")
def test_check_gemini_success(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
    avail = ModelAvailability()
    health = avail.check_gemini()

    assert health.provider == "gemini"
    assert health.status == ProviderStatus.HEALTHY
    assert health.latency_ms >= 0


@patch("subprocess.run")
def test_check_gemini_auth_fail(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="API key invalid")
    avail = ModelAvailability()
    health = avail.check_gemini()

    assert health.status == ProviderStatus.AUTH_FAILED
    assert "API key invalid" in health.error


@patch("subprocess.run")
def test_check_gemini_quota_fail(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Resource exhausted (429)")
    avail = ModelAvailability()
    health = avail.check_gemini()

    assert health.status == ProviderStatus.QUOTA_EXCEEDED


def test_check_mistral_auth_missing() -> None:
    with patch("os.getenv", return_value=None):
        avail = ModelAvailability()
        health = avail.check_mistral()
        assert health.status == ProviderStatus.AUTH_FAILED


def test_is_provider_ready_cache() -> None:
    avail = ModelAvailability()
    health_ok = ProviderHealth("gemini", ProviderStatus.HEALTHY, 10.0, datetime.now(UTC))

    with patch.object(avail, "check_gemini", return_value=health_ok) as mock_check:
        assert avail.is_provider_ready("gemini") is True
        assert mock_check.call_count == 1

        avail._health_cache["gemini"] = health_ok
        assert avail.is_provider_ready("gemini") is True
        assert mock_check.call_count == 1
