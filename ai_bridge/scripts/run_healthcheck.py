from __future__ import annotations

from ai_bridge.core.agent_registry import AgentRegistry
from ai_bridge.core.healthcheck import HealthChecker


def main() -> None:
    registry = AgentRegistry()
    registry.register("codex-main", "codex", "local://codex", ["code", "fix", "refactor"])
    checker = HealthChecker(registry)
    for health in checker.check_all():
        print(health.as_dict())


if __name__ == "__main__":
    main()
