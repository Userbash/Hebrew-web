from __future__ import annotations

from ai_bridge.agents.base_agent import BaseAgent
from ai_bridge.core.models import AgentResult, Task


class PlannerAgent(BaseAgent):
    def __init__(self, agent_id: str = "planneragent") -> None:
        super().__init__(agent_id, ['plan'])

    def run(self, task: Task) -> AgentResult:
        return self.result(task, "Created task graph and dependencies.")
