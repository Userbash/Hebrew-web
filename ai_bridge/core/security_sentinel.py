from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List, Optional

from .kernel_protocol import KernelAPI, KernelModule
from .models import Task, AgentStatus

logger = logging.getLogger("kernel_security")

@dataclass
class KernelSecuritySentinel:
    """
    Three-Tier Defense System for Distributed AI Mesh.
    1. Infrastructure: Auto-bootstrapping and health checks.
    2. Protocol: P2P Message Sanitization (TPP).
    3. User: Semantic guardrails against destructive intent.
    """
    name: str = "security_sentinel"
    _api: KernelAPI | None = None

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._api.log("info", "[SECURITY] Sentinel initialized. All tiers active.")

    def validate_action(self, task: Task) -> bool:
        """Tier 3: User Protection - Semantic Guardrails."""
        reasoning = self._api.get_module("reasoning") if self._api else None
        local_llm = self._api.get_module("local_llm") if self._api else None
        
        # Check for high-risk intent using local AI first (low latency)
        if local_llm and getattr(local_llm, "ready", False):
            prompt = f"Analyze task intent: {task.input.description}. Is it destructive or dangerous? Return YES/NO."
            resp = local_llm.query(prompt).upper()
            if "YES" in resp:
                self._api.log("error", f"[SECURITY] Destructive intent detected: {task.task_id}")
                return False
        return True

    def validate_p2p(self, sender: str, receiver: str, payload: dict) -> bool:
        """Tier 2: Protocol Security - P2P Intent Validation."""
        local_llm = self._api.get_module("local_llm") if self._api else None
        if local_llm and getattr(local_llm, "ready", False):
            return local_llm.analyze_p2p_intent(sender, receiver, payload)
        # Default to strict if local LLM is down
        return False

    def check_infrastructure(self) -> bool:
        """Tier 1: Infrastructure Integrity."""
        cold_boot = self._api.get_module("cold_boot") if self._api else None
        if cold_boot:
            report = cold_boot.ensure_infrastructure()
            return all(report.values())
        return False

    def finalize(self) -> dict[str, Any]:
        return {"tiers": ["infrastructure", "protocol", "user_guardrails"], "status": "shield_active"}
