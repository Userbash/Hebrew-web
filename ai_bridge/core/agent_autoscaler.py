from __future__ import annotations

from .agent_lifecycle import AgentLifecycleManager
from .agent_registry import AgentRegistry
from .models import AgentRecord, AgentStatus


class AgentAutoscaler:
    def __init__(self, registry: AgentRegistry, lifecycle: AgentLifecycleManager) -> None:
        self.registry = registry
        self.lifecycle = lifecycle
        self.disabled_agents: list[str] = []
        self.enabled_agents: list[str] = []

    def scale_down_idle(self) -> list[str]:
        disabled = []
        for agent in self.registry.list_agents():
            if self.lifecycle.disable_if_idle(agent):
                disabled.append(agent.id)
                self.disabled_agents.append(agent.id)
        return disabled

    def ensure_capacity(self, capability: str) -> AgentRecord | None:
        ready = [a for a in self.registry.list_agents() if capability in a.capabilities and a.status in {AgentStatus.READY, AgentStatus.IDLE, AgentStatus.DEGRADED}]
        if ready:
            return ready[0]
        for agent in self.registry.list_agents():
            if self.lifecycle.enable_for_capability(agent, capability):
                self.enabled_agents.append(agent.id)
                return agent
        return None
