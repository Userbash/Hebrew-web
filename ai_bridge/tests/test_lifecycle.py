from datetime import UTC, datetime, timedelta

from ai_bridge.core.agent_autoscaler import AgentAutoscaler
from ai_bridge.core.agent_lifecycle import AgentLifecycleManager
from ai_bridge.core.agent_registry import AgentRegistry
from ai_bridge.core.models import AgentStatus


def test_idle_agent_can_be_disabled_and_reenabled_for_capability():
    registry = AgentRegistry()
    agent = registry.register("docs-1", "docs", "local://docs", ["docs"])
    lifecycle = AgentLifecycleManager(idle_shutdown_sec=1)
    autoscaler = AgentAutoscaler(registry, lifecycle)

    lifecycle.mark_idle(agent)
    agent.metrics.idle_since = datetime.now(UTC) - timedelta(seconds=5)

    disabled = autoscaler.scale_down_idle()
    assert disabled == ["docs-1"]
    assert agent.status == AgentStatus.DISABLED

    enabled = autoscaler.ensure_capacity("docs")
    assert enabled is agent
    assert agent.status == AgentStatus.READY


def test_critical_agent_is_not_disabled():
    registry = AgentRegistry()
    agent = registry.register("codex-main", "codex", "local://codex", ["code"], critical=True)
    lifecycle = AgentLifecycleManager(idle_shutdown_sec=1)
    lifecycle.mark_idle(agent)
    agent.metrics.idle_since = datetime.now(UTC) - timedelta(seconds=5)

    assert not lifecycle.disable_if_idle(agent)
    assert agent.status == AgentStatus.IDLE
