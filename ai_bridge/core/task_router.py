from __future__ import annotations

import os

from .agent_registry import AgentRegistry
from .load_balancer import LoadBalancer
from .models import AgentRecord, AgentStatus, ExecutionPlan, Priority, Task, TaskAcceptance, TaskStatus, TaskType

CAPABILITY_BY_TASK_TYPE = {
    TaskType.PLAN: "plan",
    TaskType.CODE: "code",
    TaskType.REVIEW: "review",
    TaskType.TEST: "test",
    TaskType.DOCS: "docs",
    TaskType.FIX: "fix",
    TaskType.RESEARCH: "research",
}

HIGH_RISK_KEYWORDS = {
    "security",
    "secret",
    "production",
    "migration",
    "destructive",
    "auth",
    "rbac",
    "permission",
    "payment",
}


class TaskRouter:
    def __init__(self, registry: AgentRegistry, load_balancer: LoadBalancer) -> None:
        self.registry = registry
        self.load_balancer = load_balancer
        # Economy mode: reduce Codex calls for low/medium-risk tasks.
        self.codex_economy_mode = os.getenv("AI_BRIDGE_CODEX_ECONOMY_MODE", "true").strip().lower() in {"1", "true", "yes", "on"}

    def decompose(self, task: Task) -> ExecutionPlan:
        from .task_decomposer import TaskDecomposer

        return TaskDecomposer().decompose(task)

    def route(self, task: Task) -> TaskAcceptance:
        capability = task.required_capability or CAPABILITY_BY_TASK_TYPE[task.type]
        candidates = self._candidate_agents(capability)

        if not candidates:
            return TaskAcceptance(task.task_id, TaskStatus.REJECTED, None, self.estimate_complexity(task), f"No available agent for capability {capability}")

        preferred = self._apply_economy_policy(task, capability, candidates)
        chosen_pool = preferred or candidates

        agent = self.load_balancer.choose(chosen_pool, capability)
        if not agent:
            return TaskAcceptance(task.task_id, TaskStatus.REJECTED, None, self.estimate_complexity(task), f"No available agent for capability {capability}")

        agent.metrics.queue_depth += 1
        return TaskAcceptance(task.task_id, TaskStatus.ACCEPTED, agent.id, self.estimate_complexity(task), "Task accepted")

    def _candidate_agents(self, capability: str) -> list[AgentRecord]:
        return [
            agent
            for agent in self.registry.list_agents()
            if capability in agent.capabilities and agent.status not in {AgentStatus.OFFLINE, AgentStatus.DISABLED, AgentStatus.FAILED}
        ]

    def _apply_economy_policy(self, task: Task, capability: str, candidates: list[AgentRecord]) -> list[AgentRecord]:
        if not self.codex_economy_mode:
            return candidates

        if self._requires_codex_priority(task):
            codex_candidates = [agent for agent in candidates if agent.type.value == "codex"]
            return codex_candidates or candidates

        # Keep Codex as fallback, prefer alternative providers for non-critical work.
        non_codex = [agent for agent in candidates if agent.type.value != "codex"]

        # If the capability exists on alternative agents, route there first.
        if non_codex:
            return non_codex

        return candidates

    def _requires_codex_priority(self, task: Task) -> bool:
        if task.priority in {Priority.HIGH, Priority.CRITICAL}:
            return True

        text = task.input.description.lower()
        return any(word in text for word in HIGH_RISK_KEYWORDS)

    @staticmethod
    def estimate_complexity(task: Task) -> str:
        if task.complexity:
            return task.complexity.value
        score = len(task.input.files) + len(task.input.acceptance_criteria) + len(task.input.description) // 160
        if task.priority == Priority.CRITICAL:
            score += 2
        if score <= 2:
            return "low"
        if score <= 5:
            return "medium"
        return "high"
