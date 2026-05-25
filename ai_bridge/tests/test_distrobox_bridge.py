from __future__ import annotations

from types import SimpleNamespace

from ai_bridge.core.distrobox_bridge import DistroboxBridge, DistroboxBridgeError


def _cp(returncode: int = 0, stdout: str = "", stderr: str = ""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def test_translate_exec_flatpak_mode():
    bridge = DistroboxBridge()
    cmd = bridge.translate_exec("flatpak-spawn", "gh-dev", ["gh", "--version"])
    assert cmd == [
        "flatpak-spawn",
        "--host",
        "distrobox",
        "enter",
        "gh-dev",
        "--",
        "gh",
        "--version",
    ]


def test_box_exists_from_list_output(monkeypatch):
    bridge = DistroboxBridge()
    monkeypatch.setattr(
        DistroboxBridge,
        "_run",
        lambda self, args, mode, check=False: _cp(
            0,
            "ID | NAME   | STATUS\n1  | gh-dev | Running\n",
            "",
        ),
    )
    assert bridge.box_exists("gh-dev", "flatpak-spawn") is True


def test_ensure_gh_ready_raises_without_distrobox(monkeypatch):
    bridge = DistroboxBridge()
    monkeypatch.setattr(DistroboxBridge, "host_has_binary", lambda self, binary, mode: False)

    try:
        bridge.ensure_gh_ready("flatpak-spawn")
    except DistroboxBridgeError as exc:
        assert "distrobox is not available" in str(exc)
    else:
        raise AssertionError("Expected DistroboxBridgeError")
