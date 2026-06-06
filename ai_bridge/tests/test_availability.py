from __future__ import annotations

import socket
import subprocess
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from ai_bridge.core.availability import ModelAvailability, ProviderHealth, ProviderStatus


class _FakeSocket:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _ok_socket(*_args, **_kwargs):
    return _FakeSocket()


def test_availability_init() -> None:
    avail = ModelAvailability()
    assert avail is not None


@patch.object(ModelAvailability, "_resolve_antigravity_cli_command", return_value=["/usr/bin/agy"])
@patch("socket.create_connection", side_effect=_ok_socket)
@patch("subprocess.run")
def test_check_antigravity_success(mock_run: MagicMock, _mock_socket: MagicMock, _mock_cli: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
    avail = ModelAvailability()
    health = avail.check_antigravity()

    assert health.provider == "antigravity"
    assert health.status == ProviderStatus.HEALTHY
    assert health.latency_ms >= 0


@patch.object(ModelAvailability, "_resolve_antigravity_cli_command", return_value=["/usr/bin/agy"])
@patch("socket.create_connection", side_effect=_ok_socket)
@patch("subprocess.run")
def test_check_antigravity_auth_fail(mock_run: MagicMock, _mock_socket: MagicMock, _mock_cli: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="API key invalid")
    avail = ModelAvailability()
    health = avail.check_antigravity()

    assert health.status == ProviderStatus.AUTH_FAILED
    assert "API key invalid" in health.error


@patch.object(ModelAvailability, "_resolve_antigravity_cli_command", return_value=["/usr/bin/agy"])
@patch("socket.create_connection", side_effect=_ok_socket)
@patch("subprocess.run")
def test_check_antigravity_quota_fail(mock_run: MagicMock, _mock_socket: MagicMock, _mock_cli: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Resource exhausted (429)")
    avail = ModelAvailability()
    health = avail.check_antigravity()

    assert health.status == ProviderStatus.QUOTA_EXCEEDED


def test_check_mistral_auth_missing() -> None:
    with patch("os.getenv", return_value=None):
        avail = ModelAvailability()
        health = avail.check_mistral()
        assert health.status == ProviderStatus.AUTH_FAILED


def test_is_provider_ready_cache() -> None:
    avail = ModelAvailability()
    health_ok = ProviderHealth("antigravity", ProviderStatus.HEALTHY, 10.0, datetime.now(UTC))

    with patch.object(avail, "check_antigravity", return_value=health_ok) as mock_check:
        assert avail.is_provider_ready("antigravity") is True
        assert mock_check.call_count == 1

        avail._health_cache["antigravity"] = health_ok
        assert avail.is_provider_ready("antigravity") is True
        assert mock_check.call_count == 1


def test_check_antigravity_tcp_timeout_blocks_live_probe() -> None:
    with patch("socket.create_connection", side_effect=socket.timeout("timed out")), patch("subprocess.run") as mock_run:
        avail = ModelAvailability()
        health = avail.check_antigravity(live=True)

    assert health.status == ProviderStatus.TIMEOUT
    assert health.error == "tcp_probe_failed"
    assert health.diagnostics["tcp"]["ok"] is False
    assert mock_run.call_count == 0


def test_record_failure_updates_provider_cache() -> None:
    avail = ModelAvailability()
    health = avail.record_failure("google", "tcp_timeout", "connection timed out")

    assert health.provider == "antigravity"
    assert health.status == ProviderStatus.TIMEOUT
    assert avail.is_provider_ready("antigravity") is False
    assert health.diagnostics["runtime_failure"]["error_type"] == "tcp_timeout"
