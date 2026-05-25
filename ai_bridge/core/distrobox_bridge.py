from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass


class DistroboxBridgeError(RuntimeError):
    pass


@dataclass(slots=True)
class DistroboxBridge:
    default_box_name: str = "gh-dev"
    default_image: str = "registry.fedoraproject.org/fedora-toolbox:42"

    def _host_prefix(self, mode: str) -> list[str]:
        if mode == "flatpak-spawn":
            return ["flatpak-spawn", "--host"]
        return []

    def _run(self, args: list[str], mode: str, check: bool = False) -> subprocess.CompletedProcess[str]:
        cmd = [*self._host_prefix(mode), *args]
        return subprocess.run(cmd, capture_output=True, text=True, check=check)

    def host_has_binary(self, binary: str, mode: str) -> bool:
        probe = self._run(["sh", "-lc", f"command -v {shlex.quote(binary)} >/dev/null 2>&1"], mode)
        return probe.returncode == 0

    def box_exists(self, box_name: str, mode: str) -> bool:
        result = self._run(["distrobox", "list", "--no-color"], mode)
        if result.returncode != 0:
            return False

        for line in result.stdout.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("ID"):
                continue
            cols = [c.strip() for c in stripped.split("|")]
            if any(col == box_name for col in cols):
                return True
        return False

    def ensure_box(self, mode: str, box_name: str | None = None, image: str | None = None) -> str:
        if not self.host_has_binary("distrobox", mode):
            raise DistroboxBridgeError("distrobox is not available on host")

        name = box_name or os.getenv("HOST_BRIDGE_GH_DISTROBOX", self.default_box_name)
        selected_image = image or os.getenv("HOST_BRIDGE_GH_DISTROBOX_IMAGE", self.default_image)

        if self.box_exists(name, mode):
            return name

        create = self._run([
            "distrobox",
            "create",
            "--name",
            name,
            "--image",
            selected_image,
            "--yes",
        ], mode)
        if create.returncode != 0:
            raise DistroboxBridgeError(f"failed to create distrobox '{name}': {create.stderr.strip() or create.stdout.strip()}")
        return name

    def ensure_gh_installed(self, mode: str, box_name: str) -> None:
        check = self._run(["distrobox", "enter", box_name, "--", "sh", "-lc", "command -v gh >/dev/null 2>&1"], mode)
        if check.returncode == 0:
            return

        install_cmd = os.getenv(
            "HOST_BRIDGE_GH_INSTALL_CMD",
            "if command -v dnf >/dev/null 2>&1; then sudo dnf install -y gh; elif command -v apt-get >/dev/null 2>&1; then sudo apt-get update && sudo apt-get install -y gh; else exit 1; fi",
        )
        install = self._run(["distrobox", "enter", box_name, "--", "sh", "-lc", install_cmd], mode)
        if install.returncode != 0:
            raise DistroboxBridgeError(
                f"failed to install gh in distrobox '{box_name}': {install.stderr.strip() or install.stdout.strip()}"
            )

    def ensure_gh_ready(self, mode: str) -> str:
        box_name = self.ensure_box(mode)
        self.ensure_gh_installed(mode, box_name)
        return box_name

    def translate_exec(self, mode: str, box_name: str, command: list[str]) -> list[str]:
        if not command:
            raise DistroboxBridgeError("empty command for distrobox execution")
        return [*self._host_prefix(mode), "distrobox", "enter", box_name, "--", *command]
