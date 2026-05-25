from __future__ import annotations

from .agent_registry import AgentRegistry
from .models import AgentHealth, AgentStatus
from .availability import ModelAvailability
from ..protocols.rest_protocol import RestProtocol


class HealthChecker:
    def __init__(self, registry: AgentRegistry, rest_protocol: RestProtocol | None = None) -> None:
        self.registry = registry
        self.rest_protocol = rest_protocol or RestProtocol()
        self.availability = ModelAvailability()

    def check_providers(self) -> dict:
        return self.availability.check_all()

    def local_health(self, agent_id: str) -> AgentHealth:
        return self.registry.health_snapshot(agent_id)

    def check_agent(self, agent_id: str) -> AgentHealth:
        agent = self.registry.get(agent_id)
        if not agent:
            raise KeyError(agent_id)
        if agent.endpoint.startswith("local://"):
            return self.local_health(agent_id)
        try:
            health = self.rest_protocol.get_health(agent.endpoint)
            self.registry.update_health(health)
            return health
        except Exception as exc:  # pragma: no cover - network edge path
            health = AgentHealth(agent_id=agent.id, status=AgentStatus.OFFLINE, capabilities=agent.capabilities, last_error=str(exc))
            self.registry.update_health(health)
            return health

    def check_all(self) -> list[AgentHealth]:
        return [self.check_agent(agent.id) for agent in self.registry.list_agents()]
