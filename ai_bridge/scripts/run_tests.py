from __future__ import annotations

from ai_bridge.core.orchestrator import Orchestrator


def main() -> int:
    orchestrator = Orchestrator()
    result = orchestrator.run_test_suite(project_root=".")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
