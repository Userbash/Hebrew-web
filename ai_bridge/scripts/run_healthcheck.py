from __future__ import annotations

from ai_bridge.core.agent_registry import AgentRegistry
from ai_bridge.core.healthcheck import HealthChecker
from ai_bridge.agents.gemini_agent import GeminiAgent
from ai_bridge.core.security import SecurityManager, SecurityPolicy

def main() -> None:
    registry = AgentRegistry()
    security_manager = SecurityManager(SecurityPolicy())
    
    registry.register("codex-main", "codex", "local://codex", ["code", "fix", "refactor"])
    
    checker = HealthChecker(registry)
    
    print("\n--- Provider Availability ---")
    for provider, health in checker.check_providers().items():
        print(f"{provider}: {health.status.value} (latency: {health.latency_ms:.1f}ms)")
        if health.error:
            print(f"  Error: {health.error}")

    print("\n--- Agent Health ---")
    for health in checker.check_all():
        print(health.as_dict())

if __name__ == "__main__":
    main()
