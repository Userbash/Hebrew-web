from __future__ import annotations

from ai_bridge.core.deploy_guard import DeployGuard


def main() -> int:
    guard = DeployGuard()
    result = guard.evaluate()
    if not result.allowed:
        print("[deploy-guard] Deployment blocked:")
        for reason in result.reasons:
            print(f"- {reason}")
        return 1

    print("[deploy-guard] OK: local environment validated; deployment is allowed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
