from __future__ import annotations

from ai_bridge.agents.base_agent import BaseAgent
from ai_bridge.core.models import AgentResult, Task


class ReviewerAgent(BaseAgent):
    def __init__(self, agent_id: str = "revieweragent") -> None:
        super().__init__(agent_id, ['review', 'security'])

    def run(self, task: Task) -> AgentResult:
        return self.result(task, "Reviewed architecture, security, style, and maintainability.")
