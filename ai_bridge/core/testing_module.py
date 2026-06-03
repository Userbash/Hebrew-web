from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .kernel_protocol import KernelAPI, KernelModule


class TestingModule(KernelModule):
    name = "testing"

    def __init__(self) -> None:
        self._api: KernelAPI | None = None
        self._last_result: dict[str, Any] = {}

    def on_load(self, api: KernelAPI) -> None:
        self._api = api

    def on_unload(self) -> None:
        self._api = None

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        return None

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        return None

    def _run(self, cmd: list[str], cwd: Path | None = None) -> dict[str, Any]:
        root = cwd or Path(os.getenv("AI_BRIDGE_PROJECT_ROOT", ".")).resolve()
        proc = subprocess.run(
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": f"{root}:{os.environ.get('PYTHONPATH', '')}".rstrip(":")},
        )
        return {
            "command": cmd,
            "cwd": str(root),
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "ok": proc.returncode == 0,
        }

    def run_pytest(self, project_root: str | Path = ".", args: list[str] | None = None) -> dict[str, Any]:
        cmd = [sys.executable, "-m", "pytest", *(args or ["ai_bridge/tests"])]
        self._last_result = self._run(cmd, Path(project_root))
        return self._last_result

    def run_core_healthcheck(self, project_root: str | Path = ".") -> dict[str, Any]:
        cmd = [sys.executable, "-m", "ai_bridge.core.core_healthcheck"]
        self._last_result = self._run(cmd, Path(project_root))
        return self._last_result

    def run_verify_core(self, project_root: str | Path = ".") -> dict[str, Any]:
        cmd = [sys.executable, "-m", "ai_bridge.scripts.verify_core"]
        self._last_result = self._run(cmd, Path(project_root))
        return self._last_result

    def run_suite(self, project_root: str | Path = ".") -> dict[str, Any]:
        results = {
            "core_healthcheck": self.run_core_healthcheck(project_root),
            "verify_core": self.run_verify_core(project_root),
            "pytest": self.run_pytest(project_root),
        }
        ok = all(item.get("ok") for item in results.values())
        self._last_result = {"ok": ok, "results": results}
        return self._last_result

    def finalize(self) -> dict[str, Any]:
        return self._last_result

    def status(self) -> dict[str, Any]:
        return {
            "last_result": self._last_result,
            "project_root": os.getenv("AI_BRIDGE_PROJECT_ROOT", "."),
        }
