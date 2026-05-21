from __future__ import annotations

from datetime import UTC, datetime

from .models import AgentRecord, AgentStatus, Task

CRITICAL_AGENT_TYPES = {"planner", "codex"}
CRITICAL_CAPABILITIES = {"security", "orchestrator"}


class AgentLifecycleManager:
    def __init__(self, idle_shutdown_sec: int = 900) -> None:
        self.idle_shutdown_sec = idle_shutdown_sec

    def mark_starting(self, agent: AgentRecord) -> None:
        agent.status = AgentStatus.STARTING
        agent.metrics.status = agent.status
        agent.metrics.last_seen = datetime.now(UTC)

    def mark_ready(self, agent: AgentRecord) -> None:
        agent.status = AgentStatus.READY
        agent.disabled_reason = None
        agent.metrics.status = agent.status
        agent.metrics.idle_since = None
        agent.metrics.last_seen = datetime.now(UTC)

    def mark_busy(self, agent: AgentRecord, task: Task) -> None:
        agent.status = AgentStatus.BUSY
        agent.metrics.status = agent.status
        agent.metrics.active_tasks += 1
        agent.metrics.current_task_id = task.task_id
        agent.metrics.current_task_type = task.type.value
        agent.metrics.idle_since = None
        agent.metrics.last_seen = datetime.now(UTC)

    def mark_idle(self, agent: AgentRecord) -> None:
        agent.status = AgentStatus.IDLE
        agent.metrics.status = agent.status
        agent.metrics.active_tasks = max(0, agent.metrics.active_tasks - 1)
        agent.metrics.current_task_id = None
        agent.metrics.current_task_type = None
        agent.metrics.idle_since = datetime.now(UTC)
        agent.metrics.last_seen = datetime.now(UTC)

    def mark_failed(self, agent: AgentRecord, reason: str) -> None:
        agent.status = AgentStatus.FAILED
        agent.disabled_reason = reason
        agent.metrics.status = agent.status
        agent.metrics.failed_tasks += 1
        agent.metrics.last_seen = datetime.now(UTC)

    def disable_if_idle(self, agent: AgentRecord) -> bool:
        if self.is_critical(agent):
            return False
        if agent.metrics.active_tasks != 0 or agent.metrics.queue_depth != 0:
            return False
        if agent.status not in {AgentStatus.IDLE, AgentStatus.READY}:
            return False
        if agent.metrics.idle_since is None:
            agent.metrics.idle_since = datetime.now(UTC)
            return False
        if agent.metrics.idle_time_sec <= self.idle_shutdown_sec:
            return False
        agent.status = AgentStatus.DISABLED
        agent.disabled_reason = "idle_shutdown"
        agent.metrics.status = agent.status
        return True

    def enable_for_capability(self, agent: AgentRecord, capability: str) -> bool:
        if agent.status == AgentStatus.DISABLED and capability in agent.capabilities:
            self.mark_starting(agent)
            self.mark_ready(agent)
            return True
        return False

    @staticmethod
    def is_critical(agent: AgentRecord) -> bool:
        return agent.critical or agent.type.value in CRITICAL_AGENT_TYPES or bool(CRITICAL_CAPABILITIES.intersection(agent.capabilities))
