from __future__ import annotations
from ai_bridge.core.orchestrator import Orchestrator

class NativeOrchestratorAdapter:
    def __init__(self, orchestrator: Orchestrator) -> None:
        self.orchestrator = orchestrator
    def run(self, payload: dict[str, object]) -> dict[str, object]:
        return self.orchestrator.submit_user_task(payload, source="native_adapter")
