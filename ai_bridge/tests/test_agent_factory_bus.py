from __future__ import annotations

from ai_bridge.core.agent_factory import AgentFactory
from ai_bridge.core.message_bus import MessageBus
from ai_bridge.core.rabbitmq_bus import RabbitMQBus


def test_agent_factory_uses_inmemory_bus_by_default(monkeypatch):
    monkeypatch.delenv("AI_BRIDGE_MESSAGE_BUS_BACKEND", raising=False)
    components = AgentFactory.build()
    assert isinstance(components.message_bus, MessageBus)


def test_agent_factory_can_use_rabbitmq_bus(monkeypatch):
    monkeypatch.setenv("AI_BRIDGE_MESSAGE_BUS_BACKEND", "rabbitmq")
    components = AgentFactory.build()
    assert isinstance(components.message_bus, RabbitMQBus)
