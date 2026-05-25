from __future__ import annotations

from pathlib import Path

from ai_bridge.core.host_bridge import HostBridge, HostBridgeError


def test_whitelist_init_and_validate(tmp_path: Path):
    wl = tmp_path / "whitelist.txt"
    bridge = HostBridge(whitelist_file=wl)
    bridge.ensure_whitelist()

    assert wl.exists()
    bridge.validate(["podman", "ps"])


def test_validate_rejects_unknown_command(tmp_path: Path):
    wl = tmp_path / "whitelist.txt"
    wl.write_text("podman\n")
    bridge = HostBridge(whitelist_file=wl)

    try:
        bridge.validate(["rm", "-rf", "/"])
    except HostBridgeError as exc:
        assert "not in host bridge whitelist" in str(exc)
    else:
        raise AssertionError("Expected HostBridgeError")
