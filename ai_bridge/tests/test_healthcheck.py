from ai_bridge.core.agent_registry import AgentRegistry
from ai_bridge.core.healthcheck import HealthChecker


def test_local_healthcheck_agent():
    registry = AgentRegistry()
    registry.register("codex-main", "codex", "local://codex", ["code", "fix"])

    health = HealthChecker(registry).check_agent("codex-main")

    assert health.agent_id == "codex-main"
    assert health.status.value == "ready"
    assert "code" in health.capabilities
