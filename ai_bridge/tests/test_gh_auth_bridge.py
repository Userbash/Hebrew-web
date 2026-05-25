from __future__ import annotations

from types import SimpleNamespace

from ai_bridge.core.distrobox_bridge import DistroboxBridge
from ai_bridge.core.gh_auth_bridge import GhAuthBridge, GhAuthBridgeError


def _cp(returncode: int = 0, stdout: str = "", stderr: str = ""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def test_ensure_authenticated_uses_existing_status(monkeypatch):
    auth = GhAuthBridge()
    monkeypatch.setattr(GhAuthBridge, "_run", lambda self, mode, args, env=None: _cp(0, "", ""))

    auth.ensure_authenticated("flatpak-spawn", DistroboxBridge(), lambda name: name == "gh")


def test_ensure_authenticated_fails_without_token(monkeypatch):
    auth = GhAuthBridge()
    monkeypatch.delenv("HOST_BRIDGE_GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(GhAuthBridge, "_run", lambda self, mode, args, env=None: _cp(1, "", "unauthorized"))

    try:
        auth.ensure_authenticated("flatpak-spawn", DistroboxBridge(), lambda name: name == "gh")
    except GhAuthBridgeError as exc:
        assert "auto-login failed" in str(exc)
    else:
        raise AssertionError("Expected GhAuthBridgeError")
