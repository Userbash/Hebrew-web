from __future__ import annotations

from .agent_registry import AgentRegistry
from .load_balancer import LoadBalancer
from .models import ExecutionPlan, Priority, Task, TaskAcceptance, TaskStatus, TaskType

CAPABILITY_BY_TASK_TYPE = {
    TaskType.PLAN: "plan",
    TaskType.CODE: "code",
    TaskType.REVIEW: "review",
    TaskType.TEST: "test",
    TaskType.DOCS: "docs",
    TaskType.FIX: "fix",
    TaskType.RESEARCH: "research",
}


class TaskRouter:
    def __init__(self, registry: AgentRegistry, load_balancer: LoadBalancer) -> None:
        self.registry = registry
        self.load_balancer = load_balancer

    def decompose(self, task: Task) -> ExecutionPlan:
        from .task_decomposer import TaskDecomposer

        return TaskDecomposer().decompose(task)

    def route(self, task: Task) -> TaskAcceptance:
        capability = task.required_capability or CAPABILITY_BY_TASK_TYPE[task.type]
        agent = self.load_balancer.choose(self.registry.list_agents(), capability)
        if not agent:
            return TaskAcceptance(task.task_id, TaskStatus.REJECTED, None, self.estimate_complexity(task), f"No available agent for capability {capability}")
        agent.metrics.queue_depth += 1
        return TaskAcceptance(task.task_id, TaskStatus.ACCEPTED, agent.id, self.estimate_complexity(task), "Task accepted")

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
