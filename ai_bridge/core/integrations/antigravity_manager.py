from __future__ import annotations
import logging
from typing import Any
from ai_bridge.core.host_bridge import HostBridge

logger = logging.getLogger("AntigravityManager")

class AntigravityManager:
    def __init__(self, *, host_bridge: HostBridge | None = None) -> None:
        self.host_bridge = host_bridge or HostBridge()

    def _run_agy(self, args: list[str]) -> dict[str, Any]:
        cmd = ["agy"] + args
        try:
            # We assume HostBridge handles binary path/translation
            result = self.host_bridge.execute(cmd, timeout=30, check=False)
            return {
                "ok": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def is_ready(self) -> bool:
        # Check models and healthcheck probe
        models_res = self._run_agy(["models"])
        if not models_res["ok"]:
            return False
            
        probe_res = self._run_agy(["-p", "healthcheck: reply with ok"])
        return probe_res["ok"]

    def list_models(self) -> list[str]:
        res = self._run_agy(["models"])
        if res["ok"]:
            return [line.strip() for line in res["stdout"].splitlines() if line.strip()]
        return []

    def status(self) -> dict[str, Any]:
        return {
            "ready": self.is_ready(),
            "models": self.list_models()
        }
