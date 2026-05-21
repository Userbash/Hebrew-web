from __future__ import annotations

from datetime import UTC, datetime

from .models import AgentRecord, AgentStatus


class LoadBalancer:
    def __init__(self, overload_threshold: float = 0.85) -> None:
        self.overload_threshold = overload_threshold

    def score(self, agent: AgentRecord, capability: str) -> float:
        if agent.status in {AgentStatus.OFFLINE, AgentStatus.DISABLED, AgentStatus.FAILED}:
            return float("-inf")
        success_rate = max(0.0, min(1.0, agent.metrics.success_rate))
        availability = self._availability(agent)
        speed_score = self._speed_score(agent.metrics.avg_latency_ms)
        cost_score = self._cost_score(agent.metrics.estimated_cost or agent.metrics.token_cost)
        specialization_score = 1.0 if capability in agent.capabilities else 0.0
        overload_penalty = self._overload_penalty(agent)
        return (
            success_rate * 0.35
            + availability * 0.25
            + speed_score * 0.20
            + cost_score * 0.10
            + specialization_score * 0.10
            - overload_penalty
        ) * agent.metrics.priority_score

    def choose(self, agents: list[AgentRecord], capability: str) -> AgentRecord | None:
        candidates = [
            agent for agent in agents
            if capability in agent.capabilities and agent.status not in {AgentStatus.OFFLINE, AgentStatus.DISABLED, AgentStatus.FAILED}
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda agent: self.score(agent, capability))

    def _availability(self, agent: AgentRecord) -> float:
        if agent.status in {AgentStatus.READY, AgentStatus.IDLE}:
            base = 1.0
        elif agent.status == AgentStatus.DEGRADED:
            base = 0.45
        elif agent.status == AgentStatus.STARTING:
            base = 0.35
        elif agent.status == AgentStatus.BUSY:
            base = 0.2
        elif agent.status == AgentStatus.OVERLOADED:
            base = 0.1
        else:
            base = 0.0
        minutes_since_seen = max(0.0, (datetime.now(UTC) - agent.last_seen).total_seconds() / 60)
        return max(0.0, base - min(0.5, minutes_since_seen / 120))

    @staticmethod
    def _speed_score(avg_latency_ms: float) -> float:
        if avg_latency_ms <= 0:
            return 1.0
        return max(0.0, min(1.0, 1000.0 / (1000.0 + avg_latency_ms)))

    @staticmethod
    def _cost_score(cost: float) -> float:
        return max(0.0, min(1.0, 1.0 / (1.0 + cost)))

    def _overload_penalty(self, agent: AgentRecord) -> float:
        limit = float(agent.limits.get("max_active_tasks", 5) or 5)
        load = (agent.metrics.active_tasks + agent.metrics.queue_depth) / limit
        if load > 1:
            agent.status = AgentStatus.OVERLOADED
            agent.metrics.status = agent.status
        if load <= self.overload_threshold:
            return 0.0
        return min(0.8, load - self.overload_threshold)
