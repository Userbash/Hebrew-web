from __future__ import annotations

from ai_bridge.agents.base_agent import BaseAgent
from ai_bridge.core.models import AgentResult, Task, TaskStatus
from ai_bridge.core.security import SecurityManager
from ai_bridge.protocols.rest_protocol import RestProtocol


class ExternalAIAgent(BaseAgent):
    def __init__(self, agent_id: str, endpoint: str, capabilities: list[str], security: SecurityManager | None = None, protocol: RestProtocol | None = None) -> None:
        super().__init__(agent_id, capabilities)
        self.endpoint = endpoint
        self.security = security or SecurityManager()
        self.protocol = protocol or RestProtocol()

    def run(self, task: Task, memory_context: dict | None = None) -> AgentResult:
        payload = {
            "task_id": task.task_id,
            "type": task.type.value,
            "priority": task.priority.value,
            "input": {
                "description": task.input.description,
                "files": task.input.files,
                "constraints": task.input.constraints,
                "acceptance_criteria": task.input.acceptance_criteria,
            },
            "context": self.security.safe_context_for_external_ai({
                "project": task.context.project,
                "repo_path": task.context.repo_path,
                "branch": task.context.branch,
            }),
            "callback_url": task.callback_url,
        }
        try:
            return self.protocol.post_task(self.endpoint, payload, expected_agent_id=self.agent_id)
        except Exception as exc:  # pragma: no cover - network edge path
            return AgentResult(task.task_id, self.agent_id, TaskStatus.FAILED, {"summary": "External AI request failed", "files_changed": [], "commands_run": [], "test_results": [], "diff": ""}, 0.0, [str(exc)], [])
