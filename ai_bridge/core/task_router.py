from __future__ import annotations

import logging
import os

from .agent_registry import AgentRegistry
from .load_balancer import LoadBalancer
from .model_selector import evaluate_risk_context
from .models import AgentRecord, AgentStatus, ExecutionPlan, Priority, Task, TaskAcceptance, TaskStatus, TaskType

logger = logging.getLogger(__name__)

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
        # Economy mode: reduce Codex/OpenAI calls for low/medium-risk tasks.
        self.codex_economy_mode = os.getenv("AI_BRIDGE_CODEX_ECONOMY_MODE", "true").strip().lower() in {"1", "true", "yes", "on"}

    def decompose(self, task: Task) -> ExecutionPlan:
        from .task_decomposer import TaskDecomposer

        return TaskDecomposer().decompose(task)

    def route(self, task: Task) -> TaskAcceptance:
        capability = task.required_capability or CAPABILITY_BY_TASK_TYPE[task.type]
        candidates = self._candidate_agents(capability)

        if not candidates:
            return TaskAcceptance(task.task_id, TaskStatus.REJECTED, None, self.estimate_complexity(task), f"No available agent for capability {capability}")

        chosen_pool = self._apply_economy_policy(task, candidates)

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

    def _apply_economy_policy(self, task: Task, candidates: list[AgentRecord]) -> list[AgentRecord]:
        if not self.codex_economy_mode:
            return candidates

        complexity = self.estimate_complexity(task)
        high_risk = self._requires_openai_priority(task)

        if complexity in {"low", "medium"} and not high_risk:
            logger.info("[ROUTING] non-openai preferred for low/medium task")
            non_openai = [agent for agent in candidates if agent.provider != "openai"]
            if non_openai:
                preferred_group = self._preferred_non_openai_group(task, complexity, non_openai)
                if preferred_group:
                    return preferred_group

            fallback_openai = [agent for agent in candidates if agent.provider == "openai"]
            if fallback_openai:
                logger.warning("[FALLBACK] mistral unavailable -> openai gpt-coding-standard")
                standard = [agent for agent in fallback_openai if agent.model_name == "gpt-coding-standard"]
                return standard or fallback_openai

        openai_first = [agent for agent in candidates if agent.provider == "openai"]
        if openai_first:
            if high_risk or complexity in {"high", "critical"}:
                secure = [agent for agent in openai_first if agent.model_name == "gpt-senior-secure"]
                return secure or openai_first
            return openai_first

        return candidates

    @staticmethod
    def _preferred_non_openai_group(task: Task, complexity: str, candidates: list[AgentRecord]) -> list[AgentRecord]:
        local_agents = [agent for agent in candidates if agent.provider == "local"]
        mistral_agents = [agent for agent in candidates if agent.provider == "mistral"]
        gemini_agents = [agent for agent in candidates if agent.provider == "google"]
        other_agents = [agent for agent in candidates if agent.provider not in {"local", "mistral", "google"}]

        if complexity == "low":
            return local_agents or mistral_agents or gemini_agents or other_agents

        if task.type in {TaskType.CODE, TaskType.FIX, TaskType.TEST}:
            return mistral_agents or local_agents or gemini_agents or other_agents

        if task.type in {TaskType.DOCS, TaskType.RESEARCH, TaskType.REVIEW}:
            return gemini_agents or local_agents or mistral_agents or other_agents

        return mistral_agents or gemini_agents or local_agents or other_agents

    def _requires_openai_priority(self, task: Task) -> bool:
        if task.priority in {Priority.HIGH, Priority.CRITICAL}:
            return True
        if self.estimate_complexity(task) in {"high", "critical"}:
            return True
        text = task.input.description.lower()
        risk = evaluate_risk_context(text)
        return risk.high_risk

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
