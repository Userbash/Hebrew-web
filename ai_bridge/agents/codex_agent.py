from __future__ import annotations

from ai_bridge.agents.base_agent import BaseAgent
from ai_bridge.core.models import AgentResult, Task


class CodexAgent(BaseAgent):
    def __init__(self, agent_id: str = "codexagent") -> None:
        super().__init__(agent_id, ['code', 'fix', 'refactor'])

    def run(self, task: Task, memory_context: dict | None = None) -> AgentResult:
        return self.result(task, "Implemented requested code changes.")
