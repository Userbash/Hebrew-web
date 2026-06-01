from __future__ import annotations
from typing import Protocol, Any
class AgentRuntime(Protocol):
    def execute(self, agent_id: str, task: Any, context: dict[str, Any]) -> dict[str, Any]: ...
