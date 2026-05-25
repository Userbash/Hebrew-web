from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

from ai_bridge.core.distrobox_bridge import DistroboxBridge, DistroboxBridgeError


class GhAuthBridgeError(RuntimeError):
    pass


@dataclass(slots=True)
class GhAuthBridge:
    token_env_keys: tuple[str, ...] = ("HOST_BRIDGE_GH_TOKEN", "GITHUB_TOKEN")

    def _host_prefix(self, mode: str) -> list[str]:
        if mode == "flatpak-spawn":
            return ["flatpak-spawn", "--host"]
        return []

    def _run(self, mode: str, args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        cmd = [*self._host_prefix(mode), *args]
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        return subprocess.run(cmd, capture_output=True, text=True, env=run_env)

    def _read_token(self) -> str | None:
        for key in self.token_env_keys:
            value = os.getenv(key)
            if value:
                return value
        return None

    def _status_host(self, mode: str) -> bool:
        result = self._run(mode, ["gh", "auth", "status"])
        return result.returncode == 0

    def _status_box(self, mode: str, box_name: str) -> bool:
        result = self._run(mode, ["distrobox", "enter", box_name, "--", "gh", "auth", "status"])
        return result.returncode == 0

    def _login_host(self, mode: str, token: str) -> bool:
        result = self._run(
            mode,
            ["sh", "-lc", 'printf %s "$GH_TOKEN" | gh auth login --with-token'],
            env={"GH_TOKEN": token},
        )
        return result.returncode == 0

    def _login_box(self, mode: str, box_name: str, token: str) -> bool:
        result = self._run(
            mode,
            [
                "distrobox",
                "enter",
                box_name,
                "--",
                "sh",
                "-lc",
                'printf %s "$GH_TOKEN" | gh auth login --with-token',
            ],
            env={"GH_TOKEN": token},
        )
        return result.returncode == 0

    def ensure_authenticated(self, mode: str, distrobox_bridge: DistroboxBridge, host_has_binary: callable) -> None:
        token = self._read_token()

        if host_has_binary("gh"):
            if self._status_host(mode):
                return
            if token and self._login_host(mode, token) and self._status_host(mode):
                return
            raise GhAuthBridgeError("gh is not authenticated on host and auto-login failed")

        try:
            box_name = distrobox_bridge.ensure_gh_ready(mode)
        except DistroboxBridgeError as exc:
            raise GhAuthBridgeError(str(exc)) from exc

        if self._status_box(mode, box_name):
            return
        if token and self._login_box(mode, box_name, token) and self._status_box(mode, box_name):
            return

        if token:
            raise GhAuthBridgeError("gh auto-login failed inside distrobox")
        raise GhAuthBridgeError("gh is not authenticated and no token found in HOST_BRIDGE_GH_TOKEN/GITHUB_TOKEN")
