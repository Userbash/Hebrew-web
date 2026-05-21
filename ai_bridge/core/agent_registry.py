from __future__ import annotations

from datetime import UTC, datetime

from .models import AgentHealth, AgentRecord, AgentStatus, AgentType


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, AgentRecord] = {}

    def register(
        self,
        agent_id: str,
        agent_type: str | AgentType,
        endpoint: str,
        capabilities: list[str],
        limits: dict | None = None,
        access_key_ref: str | None = None,
        model_name: str = "local-small",
        provider: str = "local",
        critical: bool = False,
    ) -> AgentRecord:
        if not agent_id:
            raise ValueError("agent_id is required")
        if not endpoint:
            raise ValueError("endpoint is required")
        if not capabilities:
            raise ValueError("capabilities are required")
        record = AgentRecord(
            id=agent_id,
            type=AgentType(agent_type),
            endpoint=endpoint,
            capabilities=sorted(set(capabilities)),
            limits=limits or {},
            access_key_ref=access_key_ref,
            critical=critical,
            model_name=model_name,
            provider=provider,
        )
        self._agents[agent_id] = record
        return record

    def unregister(self, agent_id: str) -> None:
        self._agents.pop(agent_id, None)

    def get(self, agent_id: str) -> AgentRecord | None:
        return self._agents.get(agent_id)

    def list_agents(self) -> list[AgentRecord]:
        return list(self._agents.values())

    def by_capability(self, capability: str, include_disabled: bool = False) -> list[AgentRecord]:
        agents = [agent for agent in self._agents.values() if agent.has_capability(capability)]
        if include_disabled:
            return agents
        return [agent for agent in agents if agent.status != AgentStatus.DISABLED]

    def update_health(self, health: AgentHealth) -> None:
        agent = self._agents.get(health.agent_id)
        if not agent:
            return
        agent.status = health.status
        agent.capabilities = sorted(set(health.capabilities))
        agent.metrics.active_tasks = health.active_tasks
        agent.metrics.queue_depth = health.queue_depth
        agent.metrics.avg_latency_ms = health.avg_latency_ms
        agent.metrics.success_rate = health.success_rate
        agent.metrics.error_rate = max(0.0, min(1.0, 1.0 - health.success_rate))
        agent.metrics.status = health.status
        agent.metrics.last_seen = datetime.now(UTC)
        agent.last_seen = datetime.now(UTC)

    def health_snapshot(self, agent_id: str) -> AgentHealth:
        agent = self._agents[agent_id]
        return AgentHealth(
            agent_id=agent.id,
            status=agent.status,
            capabilities=agent.capabilities,
            active_tasks=agent.metrics.active_tasks,
            queue_depth=agent.metrics.queue_depth,
            avg_latency_ms=agent.metrics.avg_latency_ms,
            success_rate=agent.metrics.success_rate,
        )

    def ready_agents(self) -> list[AgentRecord]:
        return [a for a in self._agents.values() if a.status in {AgentStatus.READY, AgentStatus.IDLE, AgentStatus.DEGRADED}]
