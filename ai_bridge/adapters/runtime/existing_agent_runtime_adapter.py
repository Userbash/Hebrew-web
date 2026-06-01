from __future__ import annotations
from typing import Any
from ai_bridge.core.orchestrator import Orchestrator

class ExistingAgentRuntimeAdapter:
    def __init__(self, orchestrator: Orchestrator) -> None:
        self.orchestrator = orchestrator
    def execute(self, agent_id: str, task: Any, context: dict[str, Any]) -> dict[str, Any]:
        _ = context
        result = self.orchestrator.local_agents[agent_id].run(task)
        return {"agent_id": agent_id, "status": result.status.value, "output": result.output}
