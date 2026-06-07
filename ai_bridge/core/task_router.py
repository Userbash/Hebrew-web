from __future__ import annotations

import logging
import os
from datetime import datetime, UTC

from .agent_registry import AgentRegistry
from .load_balancer import LoadBalancer, UNROUTABLE_AGENT_STATUSES, is_agent_routable
from .model_selector import evaluate_risk_context
from .models import AgentRecord, ExecutionPlan, Priority, Task, TaskAcceptance, TaskStatus, TaskType, TaskEnvelope

logger = logging.getLogger(__name__)

SOURCECRAFT_KEYWORDS = ("sourcecraft", "src ", " src", "repo", "repository", "pull request", "pr ", " pr", "issue", "release", "branch", "tag", "changelog", "quota", "status")
SOURCECRAFT_ROUTABLE_TASK_TYPES = {TaskType.PLAN, TaskType.DOCS, TaskType.RESEARCH}


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
        self.codex_economy_mode = os.getenv("AI_BRIDGE_CODEX_ECONOMY_MODE", "true").strip().lower() in {"1", "true", "yes", "on"}
        self._api: Any | None = None

    def set_api(self, api: Any) -> None:
        self._api = api

    @staticmethod
    def _is_sourcecraft_work(task: Task) -> bool:
        text = " ".join([task.input.description, *task.input.constraints, *task.input.files]).lower()
        return task.required_capability == "sourcecraft" or (task.type in SOURCECRAFT_ROUTABLE_TASK_TYPES and any(keyword in text for keyword in SOURCECRAFT_KEYWORDS))

    def decompose(self, task: Task) -> ExecutionPlan:
        from .task_decomposer import TaskDecomposer
        return TaskDecomposer().decompose(task)

    def route_envelope(self, envelope: TaskEnvelope) -> TaskAcceptance:
        """Route a network-like TaskEnvelope based on policy, QoS, and risk."""
        capability = envelope.target_capability
        sourcecraft_task = capability == "sourcecraft"
        candidates = [agent for agent in self._candidate_agents(capability) if is_agent_routable(agent, envelope.priority)]

        if not candidates:
            if sourcecraft_task:
                return TaskAcceptance(envelope.task_id, TaskStatus.ACCEPTED, "orchestrator", "high", "SourceCraft role handled by orchestrator module")
            return TaskAcceptance(envelope.task_id, TaskStatus.REJECTED, None, "high", f"No available agent for capability {capability}")
            
        if envelope.deadline and datetime.now(UTC) > envelope.deadline:
            logger.warning(f"Envelope {envelope.task_id} deadline exceeded. Rejecting.")
            return TaskAcceptance(envelope.task_id, TaskStatus.REJECTED, None, "high", "Deadline exceeded before routing")
            
        if envelope.security_policy.requires_approval:
            logger.info(f"Envelope {envelope.task_id} requires human approval.")
            return TaskAcceptance(envelope.task_id, TaskStatus.WAITING_INPUT, None, "critical", "Requires manual security approval")

        chosen_pool = self._apply_economy_policy_envelope(envelope, candidates)

        agent = self._select_best_agent(chosen_pool, envelope)
        if not agent:
            return TaskAcceptance(envelope.task_id, TaskStatus.REJECTED, None, "high", f"No healthy agent for capability {capability} under QoS requirements")

        agent.metrics.queue_depth += 1
        return TaskAcceptance(envelope.task_id, TaskStatus.ACCEPTED, agent.id, "medium", "Task accepted")

    def _select_best_agent(self, candidates: list[AgentRecord], envelope: TaskEnvelope) -> AgentRecord | None:
        def score(a: AgentRecord) -> float:
            base = 100.0
            base -= a.metrics.queue_depth * 10
            base -= a.metrics.avg_latency_ms * 0.01
            base -= a.metrics.error_rate * 50
            if envelope.priority in {Priority.HIGH, Priority.CRITICAL, "high", "critical"}:
                base += a.kpi.quality_score * 20
            return base

        valid_candidates = [c for c in candidates if score(c) > 0]
        if not valid_candidates:
            return None
            
        return max(valid_candidates, key=score)

    def route(self, task: Task) -> TaskAcceptance:
        capability = task.required_capability or CAPABILITY_BY_TASK_TYPE[task.type]
        sourcecraft_task = self._is_sourcecraft_work(task)
        if sourcecraft_task and capability != "sourcecraft":
            capability = "sourcecraft"

        candidates = [agent for agent in self._candidate_agents(capability) if is_agent_routable(agent, task.priority)]

        if not candidates:
            if capability == "sourcecraft" or sourcecraft_task:
                return TaskAcceptance(task.task_id, TaskStatus.ACCEPTED, "orchestrator", self.estimate_complexity(task), "SourceCraft role handled by orchestrator module")
            return TaskAcceptance(task.task_id, TaskStatus.REJECTED, None, self.estimate_complexity(task), f"No available agent for capability {capability}")

        chosen_pool = self._apply_economy_policy(task, candidates)

        agent = self.load_balancer.choose(chosen_pool, capability, task.priority)
        if not agent:
            if capability == "sourcecraft" or sourcecraft_task:
                return TaskAcceptance(task.task_id, TaskStatus.ACCEPTED, "orchestrator", self.estimate_complexity(task), "SourceCraft role handled by orchestrator module")
            return TaskAcceptance(task.task_id, TaskStatus.REJECTED, None, self.estimate_complexity(task), f"No available agent for capability {capability}")

        agent.metrics.queue_depth += 1
        return TaskAcceptance(task.task_id, TaskStatus.ACCEPTED, agent.id, self.estimate_complexity(task), "Task accepted")

    def _candidate_agents(self, capability: str) -> list[AgentRecord]:
        return [
            agent
            for agent in self.registry.list_agents()
            if capability in agent.capabilities and agent.status not in UNROUTABLE_AGENT_STATUSES
        ]

    def _apply_economy_policy_envelope(self, envelope: TaskEnvelope, candidates: list[AgentRecord]) -> list[AgentRecord]:
        if not self.codex_economy_mode:
            return candidates
            
        risk = evaluate_risk_context(envelope.payload.objective)
        
        if not risk.high_risk and envelope.priority not in {Priority.CRITICAL, Priority.HIGH, "critical", "high"}:
            non_openai = [agent for agent in candidates if agent.provider != "openai"]
            if non_openai:
                return non_openai
        return candidates

    def _apply_economy_policy(self, task: Task, candidates: list[AgentRecord]) -> list[AgentRecord]:
        if not self.codex_economy_mode:
            return candidates

        complexity = self.estimate_complexity(task)
        high_risk = self._requires_openai_priority(task)

        if complexity in {"low", "medium"} and not high_risk:
            non_openai = [agent for agent in candidates if agent.provider != "openai"]
            if non_openai:
                preferred_group = self._preferred_non_openai_group(task, complexity, non_openai)
                if preferred_group:
                    return preferred_group

            fallback_openai = [agent for agent in candidates if agent.provider == "openai"]
            if fallback_openai:
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
        antigravity_agents = [agent for agent in candidates if agent.provider == "antigravity"]
        other_agents = [agent for agent in candidates if agent.provider not in {"local", "mistral", "antigravity"}]

        if complexity == "low":
            return local_agents or mistral_agents or antigravity_agents or other_agents

        if task.type in {TaskType.CODE, TaskType.REVIEW}:
            return antigravity_agents or mistral_agents or local_agents or other_agents

        if task.type in {TaskType.FIX, TaskType.TEST}:
            return mistral_agents or antigravity_agents or local_agents or other_agents

        if task.type in {TaskType.DOCS, TaskType.RESEARCH}:
            return antigravity_agents or local_agents or mistral_agents or other_agents

        return antigravity_agents or mistral_agents or local_agents or other_agents

    def _requires_openai_priority(self, task: Task) -> bool:
        if task.priority in {Priority.HIGH, Priority.CRITICAL}:
            return True
        if self.estimate_complexity(task) in {"high", "critical"}:
            return True
        text = task.input.description.lower()
        risk = evaluate_risk_context(text)
        return risk.high_risk

    def estimate_complexity(self, task: Task) -> str:
        if task.complexity:
            return task.complexity.value
        
        if self._api:
            intel = self._api.get_module("intelligence")
            if intel:
                analysis = intel.estimate_complexity(task)
                if analysis:
                    return analysis.complexity

        # Fallback to heuristic
        score = len(task.input.files) + len(task.input.acceptance_criteria) + len(task.input.description) // 160
        if task.priority == Priority.CRITICAL:
            score += 2
        if score <= 2:
            return "low"
        if score <= 5:
            return "medium"
        return "high"
