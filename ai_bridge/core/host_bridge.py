from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from ai_bridge.core.distrobox_bridge import DistroboxBridge, DistroboxBridgeError
from ai_bridge.core.gh_auth_bridge import GhAuthBridge, GhAuthBridgeError


class HostBridgeError(RuntimeError):
    pass


@dataclass(slots=True)
class HostBridge:
    whitelist_file: Path = Path("ai_bridge/scripts/bridge/whitelist.txt")
    distrobox_bridge: DistroboxBridge = field(default_factory=DistroboxBridge)
    gh_auth_bridge: GhAuthBridge = field(default_factory=GhAuthBridge)
    default_allowlist: list[str] = field(default_factory=lambda: [
        "git",
        "gh",
        "distrobox",
        "distrobox-host-exec",
        "podman",
        "docker",
        "docker-compose",
        "podman-compose",
        "systemctl",
        "npm",
        "node",
        "npx",
        "ls",
        "which",
        "cat",
        "bash",
        "curl",
        "netstat",
        "ss",
        "ip",
    ])

    def ensure_whitelist(self) -> None:
        self.whitelist_file.parent.mkdir(parents=True, exist_ok=True)
        if self.whitelist_file.exists():
            return
        self.whitelist_file.write_text("\n".join(self.default_allowlist) + "\n")

    def allowlist(self) -> set[str]:
        self.ensure_whitelist()
        return {line.strip() for line in self.whitelist_file.read_text().splitlines() if line.strip() and not line.strip().startswith("#")}

    def validate(self, command: list[str]) -> None:
        if not command:
            raise HostBridgeError("Empty command")
        if command[0] not in self.allowlist():
            raise HostBridgeError(f"Command '{command[0]}' is not in host bridge whitelist")

    def detect_mode(self) -> str:
        if shutil.which("flatpak-spawn"):
            return "flatpak-spawn"
        if os.getenv("IS_CONTAINER") or Path("/.dockerenv").exists():
            return "container"
        return "direct"

    def _host_has_binary(self, binary: str) -> bool:
        result = subprocess.run(
            ["flatpak-spawn", "--host", "sh", "-lc", f"command -v {shlex.quote(binary)} >/dev/null 2>&1"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def _translate_podman_compose(self, command: list[str]) -> list[str]:
        compose_args = command[2:]

        if self._host_has_binary("docker"):
            return ["flatpak-spawn", "--host", "docker", "compose", *compose_args]
        if self._host_has_binary("docker-compose"):
            return ["flatpak-spawn", "--host", "docker-compose", *compose_args]
        if self._host_has_binary("podman-compose"):
            return ["flatpak-spawn", "--host", "podman-compose", *compose_args]

        raise HostBridgeError("No compose provider found on host (docker compose / docker-compose / podman-compose)")

    def _translate_gh(self, command: list[str], mode: str) -> list[str]:
        gh_args = command[1:]

        if mode == "flatpak-spawn":
            if self._host_has_binary("gh"):
                return ["flatpak-spawn", "--host", "gh", *gh_args]
            try:
                box_name = self.distrobox_bridge.ensure_gh_ready(mode)
                return self.distrobox_bridge.translate_exec(mode, box_name, ["gh", *gh_args])
            except DistroboxBridgeError as exc:
                raise HostBridgeError(str(exc)) from exc

        if shutil.which("gh"):
            return ["gh", *gh_args]

        try:
            box_name = self.distrobox_bridge.ensure_gh_ready(mode)
            return self.distrobox_bridge.translate_exec(mode, box_name, ["gh", *gh_args])
        except DistroboxBridgeError as exc:
            raise HostBridgeError(str(exc)) from exc

    def translate(self, command: list[str]) -> list[str]:
        mode = self.detect_mode()

        if command[0] == "gh":
            return self._translate_gh(command, mode)

        if mode == "flatpak-spawn":
            if len(command) >= 2 and command[0] == "podman" and command[1] == "compose":
                return self._translate_podman_compose(command)
            return ["flatpak-spawn", "--host", *command]

        if mode == "direct":
            if len(command) >= 2 and command[0] == "podman" and command[1] == "compose":
                if shutil.which("docker"):
                    return ["docker", "compose", *command[2:]]
                if shutil.which("docker-compose"):
                    return ["docker-compose", *command[2:]]
                if shutil.which("podman-compose"):
                    return ["podman-compose", *command[2:]]
                raise HostBridgeError("No local compose provider available")
            return command

        return command

    def execute(
        self,
        command: list[str],
        *,
        timeout: int | None = None,
        capture_output: bool = True,
        text: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        self.validate(command)
        mode = self.detect_mode()
        if command[0] == "gh":
            try:
                self.gh_auth_bridge.ensure_authenticated(mode, self.distrobox_bridge, self._host_has_binary)
            except GhAuthBridgeError as exc:
                raise HostBridgeError(str(exc)) from exc

        translated = self._translate_gh(command, mode) if command[0] == "gh" else self.translate(command)
        return subprocess.run(translated, timeout=timeout, capture_output=capture_output, text=text, check=check)
