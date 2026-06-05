from __future__ import annotations

from dataclasses import dataclass

from .agent_registry import AgentRegistry
from .models import (
    AgentReadiness,
    AgentRecord,
    AgentStatus,
    Complexity,
    Priority,
    ReadinessLevel,
    SchedulerDecision,
    Task,
    TaskType,
    TaskWeight,
    TaskEnvelope,
    TaskGraph
)
from .task_router import CAPABILITY_BY_TASK_TYPE

ORCHESTRATOR_TASK_TYPES = {TaskType.PLAN}
ORCHESTRATOR_CAPABILITIES = {"security", "auth", "database", "architecture", "orchestrator", "sourcecraft"}
SOURCECRAFT_KEYWORDS = ("sourcecraft", "src ", " src", "repo", "repository", "pull request", "pr ", " pr", "issue", "release", "branch", "tag", "changelog", "quota", "status")
SOURCECRAFT_ROUTABLE_TASK_TYPES = {TaskType.PLAN, TaskType.DOCS, TaskType.RESEARCH}
BLOCKED_STATUSES = {
    AgentStatus.OFFLINE,
    AgentStatus.DISABLED,
    AgentStatus.FAILED,
    AgentStatus.UNREACHABLE,
    AgentStatus.MAINTENANCE,
    AgentStatus.DRAINING,
    AgentStatus.OVERLOADED,
}
LOW_COST_BUSY_TYPES = {TaskType.DOCS, TaskType.RESEARCH}

@dataclass(slots=True)
class RetryPolicy:
    retry_limit: int = 3
    timeout_sec: int = 900
    escalate_after_failures: int = 3

class SmartScheduler:
    """Priority-aware scheduler for hybrid orchestrator and P2P routing."""

    def __init__(self, registry: AgentRegistry, retry_policy: RetryPolicy | None = None) -> None:
        self.registry = registry
        self.retry_policy = retry_policy or RetryPolicy()
        self.decisions: list[SchedulerDecision] = []

    @staticmethod
    def _is_sourcecraft_work(text: str) -> bool:
        normalized = text.lower()
        return any(keyword in normalized for keyword in SOURCECRAFT_KEYWORDS)

    def schedule_envelope(self, envelope: TaskEnvelope, graph: TaskGraph | None = None) -> SchedulerDecision:
        """Schedule a network-like TaskEnvelope, enforcing DAG dependency checks and security policies."""
        if graph and envelope.dependencies:
            for dep in envelope.dependencies:
                if getattr(graph, f"{dep}_status", None) == "failed":
                    decision = SchedulerDecision(envelope.task_id, "orchestrator", None, True, "Dependency failed", 0.0)
                    self.decisions.append(decision)
                    return decision

        priority_map = {Priority.LOW: 2, Priority.NORMAL: 5, Priority.HIGH: 8, Priority.CRITICAL: 10, "low": 2, "normal": 5, "high": 8, "critical": 10}
        p_val = priority_map.get(envelope.priority, 5)
        
        text = str(envelope.payload.objective).lower()
        risky_terms = {"rollback", "migration", "secret", "security", "auth", "database", "billing", "api", "schema"}
        sourcecraft_task = envelope.target_capability == "sourcecraft"
        requires_orchestrator = (
            envelope.priority in {Priority.CRITICAL, "critical"}
            or envelope.target_capability in ORCHESTRATOR_CAPABILITIES
            or sourcecraft_task
            or any(term in text for term in risky_terms)
        )

        task_score = p_val * 0.5 + (8 if requires_orchestrator else 2) * 0.5
        
        candidates = [agent for agent in self.registry.list_agents() if envelope.target_capability in agent.capabilities or envelope.target_capability == "any"]
        
        if not candidates:
            decision = SchedulerDecision(envelope.task_id, "orchestrator", None, True, "No ready agent for required capability", task_score)
        else:
            agent = max(candidates, key=lambda a: self.agent_score(a, envelope.target_capability))
            score = self.agent_score(agent, envelope.target_capability)
            readiness = self.readiness(agent)
            
            if requires_orchestrator:
                decision = SchedulerDecision(envelope.task_id, "orchestrator", agent.id, True, "High-risk or strategic task", task_score, score, readiness.readiness)
            else:
                decision = SchedulerDecision(envelope.task_id, "p2p", agent.id, False, "Local low-risk task can use direct agent workflow", task_score, score, readiness.readiness)
                
        self.decisions.append(decision)
        return decision

    def task_weight(self, task: Task) -> TaskWeight:
        priority_map = {
            Priority.LOW: 2,
            Priority.NORMAL: 5,
            Priority.HIGH: 8,
            Priority.CRITICAL: 10,
        }
        complexity_map = {
            None: 3,
            Complexity.LOW: 2,
            Complexity.MEDIUM: 5,
            Complexity.HIGH: 8,
            Complexity.CRITICAL: 10,
        }
        risk = 8 if self.requires_orchestrator(task) else 3
        if task.type in {TaskType.FIX, TaskType.TEST, TaskType.REVIEW}:
            risk = max(2, risk - 2)
        return TaskWeight(
            task_id=task.task_id,
            priority=priority_map[task.priority],
            risk=risk,
            complexity=complexity_map[task.complexity],
            urgency=9 if task.priority == Priority.CRITICAL else priority_map[task.priority],
            business_value=8 if task.priority in {Priority.HIGH, Priority.CRITICAL} else 5,
            dependency_count=len(task.dependencies),
            estimated_cost=max(1, len(task.input.files) + len(task.input.description) // 240),
            requires_review=task.priority in {Priority.HIGH, Priority.CRITICAL} or risk >= 7,
        )

    def requires_orchestrator(self, task: Task) -> bool:
        capability = task.required_capability or CAPABILITY_BY_TASK_TYPE[task.type]
        text = " ".join([task.input.description, *task.input.constraints, *task.input.files]).lower()
        risky_terms = {"rollback", "migration", "secret", "security", "auth", "database", "billing", "api", "schema"}
        return (
            task.priority == Priority.CRITICAL
            or task.type in ORCHESTRATOR_TASK_TYPES
            or task.complexity == Complexity.CRITICAL
            or capability in ORCHESTRATOR_CAPABILITIES
            or (task.type in SOURCECRAFT_ROUTABLE_TASK_TYPES and self._is_sourcecraft_work(text))
            or any(term in text for term in risky_terms)
        )

    def readiness(self, agent: AgentRecord) -> AgentReadiness:
        max_tasks = int(agent.limits.get("max_active_tasks", 5) or 5)
        current_tasks = agent.metrics.active_tasks + agent.metrics.queue_depth
        load = min(1.0, current_tasks / max(1, max_tasks))
        if agent.status in {AgentStatus.IDLE, AgentStatus.READY} and load <= 0.2:
            level = ReadinessLevel.HOT
        elif agent.status in {AgentStatus.STANDBY, AgentStatus.STARTING, AgentStatus.WARMING_UP}:
            level = ReadinessLevel.WARM
        elif agent.status in {AgentStatus.OFFLINE, AgentStatus.SLEEPING, AgentStatus.DISABLED}:
            level = ReadinessLevel.COLD
        else:
            level = ReadinessLevel.WARM if load < 0.85 else ReadinessLevel.COLD
        return AgentReadiness(
            agent_id=agent.id,
            status=agent.status,
            readiness=level,
            current_tasks=current_tasks,
            max_tasks=max_tasks,
            load=load,
            capabilities=agent.capabilities,
            latency_ms=agent.metrics.avg_latency_ms,
            last_heartbeat=agent.metrics.last_seen.isoformat(),
        )

    def agent_score(self, agent: AgentRecord, capability: str) -> float:
        if agent.status in BLOCKED_STATUSES:
            return float("-inf")
        capability_match = 1.0 if capability in agent.capabilities else 0.0
        readiness = self.readiness(agent)
        availability = {ReadinessLevel.HOT: 1.0, ReadinessLevel.WARM: 0.65, ReadinessLevel.COLD: 0.2}[readiness.readiness]
        low_latency = max(0.0, min(1.0, 1000.0 / (1000.0 + agent.metrics.avg_latency_ms)))
        low_load = max(0.0, 1.0 - readiness.load)
        success_rate = max(0.0, min(1.0, agent.metrics.success_rate))
        return capability_match * 0.35 + availability * 0.25 + low_latency * 0.15 + low_load * 0.15 + success_rate * 0.10

    def choose_agent(self, task: Task) -> tuple[AgentRecord | None, float, AgentReadiness | None]:
        capability = task.required_capability or CAPABILITY_BY_TASK_TYPE[task.type]
        candidates = [agent for agent in self.registry.list_agents() if capability in agent.capabilities]
        if task.type not in LOW_COST_BUSY_TYPES:
            candidates = [agent for agent in candidates if agent.status != AgentStatus.BUSY]
        if not candidates:
            return None, 0.0, None
        agent = max(candidates, key=lambda item: self.agent_score(item, capability))
        score = self.agent_score(agent, capability)
        if score == float("-inf"):
            return None, 0.0, None
        return agent, score, self.readiness(agent)

    def schedule(self, task: Task) -> SchedulerDecision:
        weight = self.task_weight(task)
        agent, score, readiness = self.choose_agent(task)
        requires_orchestrator = self.requires_orchestrator(task)
        if not agent:
            reason = "SourceCraft role handled by orchestrator module" if (task.type in SOURCECRAFT_ROUTABLE_TASK_TYPES and self._is_sourcecraft_work(task.input.description)) or (task.required_capability == "sourcecraft") else "No ready agent for required capability"
            decision = SchedulerDecision(task.task_id, "orchestrator", None, True, reason, weight.task_score)
        elif requires_orchestrator:
            decision = SchedulerDecision(task.task_id, "orchestrator", agent.id, True, "High-risk or strategic task", weight.task_score, score, readiness.readiness if readiness else None)
        else:
            decision = SchedulerDecision(task.task_id, "p2p", agent.id, False, "Local low-risk task can use direct agent workflow", weight.task_score, score, readiness.readiness if readiness else None)
        self.decisions.append(decision)
        return decision

    def should_escalate(self, task: Task, retry_count: int, *, architecture_changed: bool = False, security_affected: bool = False, conflict_detected: bool = False) -> bool:
        return (
            retry_count > self.retry_policy.retry_limit
            or self.requires_orchestrator(task)
            or architecture_changed
            or security_affected
            or conflict_detected
        )
