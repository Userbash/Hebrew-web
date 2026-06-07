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


@patch("ai_bridge.core.availability.AntigravityManager")
@patch("socket.create_connection", side_effect=_ok_socket)
def test_check_antigravity_success(mock_manager: MagicMock, _mock_socket: MagicMock) -> None:
    instance = mock_manager.return_value
    instance.is_ready.return_value = True
    instance.list_models.return_value = ["model1", "model2"]

    avail = ModelAvailability()
    health = avail.check_antigravity()

    assert health.provider == "antigravity"
    assert health.status == ProviderStatus.HEALTHY

    assert health.latency_ms >= 0


# @patch("ai_bridge.core.availability.AntigravityManager")
# @patch("socket.create_connection", side_effect=_ok_socket)
# def test_check_antigravity_auth_fail(mock_manager: MagicMock, _mock_socket: MagicMock) -> None:
#     instance = mock_manager.return_value
#     instance.is_ready.return_value = False
#     instance.list_models.return_value = []
#     
#     avail = ModelAvailability()
#     health = avail.check_antigravity()
#
#     assert health.status == ProviderStatus.DEGRADED
#
# @patch("ai_bridge.core.availability.AntigravityManager")
# @patch("socket.create_connection", side_effect=_ok_socket)
# def test_check_antigravity_quota_fail(mock_manager: MagicMock, _mock_socket: MagicMock) -> None:
#     instance = mock_manager.return_value
#     instance.is_ready.return_value = False
#     instance.list_models.return_value = []
#     
#     avail = ModelAvailability()
#     health = avail.check_antigravity()
#
#     assert health.status == ProviderStatus.DEGRADED
def test_check_mistral_auth_missing() -> None:
    with patch("os.getenv") as mock_env:
        # Mock MISTRAL_API_KEY to return None, others to return default
        def env_side_effect(key, default=None):
            if key == "MISTRAL_API_KEY":
                return None
            return default
        mock_env.side_effect = env_side_effect
        
        avail = ModelAvailability()
        health = avail.check_mistral()
        assert health.status == ProviderStatus.DEGRADED


def test_is_provider_ready_cache() -> None:
    avail = ModelAvailability()
    health_ok = ProviderHealth("antigravity", ProviderStatus.HEALTHY, 10.0, datetime.now(UTC))

    avail._health_cache["antigravity"] = health_ok
    assert avail.is_provider_ready("antigravity") is True


def test_check_antigravity_tcp_timeout_blocks_live_probe() -> None:
    with patch("socket.create_connection", side_effect=socket.timeout("timed out")):
        avail = ModelAvailability()
        health = avail.check_antigravity(live=True)

    assert health.status == ProviderStatus.TIMEOUT
    assert health.error == "tcp_probe_failed"
    assert health.diagnostics["tcp"]["ok"] is False


def test_record_failure_updates_provider_cache() -> None:
    avail = ModelAvailability()
    health = avail.record_failure("google", "tcp_timeout", "connection timed out")

    assert health.provider == "antigravity"
    assert health.status == ProviderStatus.TIMEOUT
    assert avail.is_provider_ready("antigravity") is False
    assert health.diagnostics["error_type"] == "tcp_timeout"
