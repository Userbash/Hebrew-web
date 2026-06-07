from __future__ import annotations

import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any

from .kernel_protocol import KernelAPI, KernelModule
from .host_bridge import HostBridge

logger = logging.getLogger("cold_boot")

@dataclass
class ColdBootModule:
    """
    Automated bootstrap module for AI Infrastructure.
    Detects missing containers/services and triggers self-healing.
    """
    name: str = "cold_boot"
    _api: KernelAPI | None = None
    _host: HostBridge = field(default_factory=HostBridge)

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._api.log("info", "[COLD_BOOT] Infrastructure Sentinel active.")
        
        if os.getenv("AI_BRIDGE_AUTO_BOOTSTRAP", "true").lower() == "true":
            self.ensure_infrastructure()

    def ensure_infrastructure(self) -> dict[str, Any]:
        """Checks and starts missing AI components."""
        report = {"ollama": False, "orchestrator_container": False, "repaired": []}
        
        # 1. Check Local LLM (Ollama)
        local_llm = self._api.get_module("local_llm") if self._api else None
        if local_llm and not getattr(local_llm, "ready", False):
            self._api.log("warn", "[COLD_BOOT] Local LLM offline. Attempting bootstrap...")
            # Try to start via host script
            try:
                # Assuming scripts/start_ai_bridge_stack.sh handles this
                self._host.execute(["bash", "scripts/start_ai_bridge_stack.sh"])
                report["repaired"].append("local_llm_stack")
                # Wait for boot
                time.sleep(5)
            except Exception as e:
                self._api.log("error", f"[COLD_BOOT] Bootstrap failed: {e}")

        # 2. Check Podman Container availability
        try:
            result = self._host.execute(["podman", "ps", "--filter", "name=hebrew_ai_orchestrator", "--format", "{{.Status}}"])
            if "Up" in result.stdout:
                report["orchestrator_container"] = True
            else:
                self._api.log("warn", "[COLD_BOOT] Orchestrator container not running. Re-stacking...")
                self._host.execute(["bash", "scripts/start_ai_bridge_stack.sh"])
                report["repaired"].append("orchestrator_container")
        except Exception:
            pass

        return report

    def on_unload(self) -> None:
        pass

    def finalize(self) -> dict[str, Any]:
        return {"status": "sentinel_active"}
