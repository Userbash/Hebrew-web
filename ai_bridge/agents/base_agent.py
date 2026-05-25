from __future__ import annotations

from abc import ABC, abstractmethod

from ai_bridge.core.host_bridge import HostBridge
from ai_bridge.core.models import AgentHealth, AgentResult, AgentStatus, Task, TaskStatus


class BaseAgent(ABC):
    def __init__(self, agent_id: str, capabilities: list[str]) -> None:
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.active_tasks = 0
        self.queue_depth = 0
        self.avg_latency_ms = 0.0
        self.success_rate = 1.0
        self.last_error: str | None = None
        self.host_bridge: HostBridge | None = None

    def health(self) -> AgentHealth:
        return AgentHealth(
            agent_id=self.agent_id,
            status=AgentStatus.BUSY if self.active_tasks else AgentStatus.READY,
            capabilities=self.capabilities,
            active_tasks=self.active_tasks,
            queue_depth=self.queue_depth,
            avg_latency_ms=self.avg_latency_ms,
            success_rate=self.success_rate,
            last_error=self.last_error,
        )


    def set_host_bridge(self, bridge: HostBridge) -> None:
        self.host_bridge = bridge

    @abstractmethod
    def run(self, task: Task, memory_context: dict | None = None) -> AgentResult:
        raise NotImplementedError

    def result(self, task: Task, summary: str, status: TaskStatus = TaskStatus.DONE, confidence: float = 0.9, errors: list[str] | None = None) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status=status,
            output={
                "summary": summary,
                "files_changed": [],
                "commands_run": [],
                "test_results": [],
                "diff": "",
            },
            confidence=confidence,
            errors=errors or [],
            next_recommendations=[],
        )
