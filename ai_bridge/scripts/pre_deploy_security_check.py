from __future__ import annotations

from ai_bridge.core.deploy_guard import DeployGuard
from ai_bridge.core.security_gate import SecurityGate


def main() -> int:
    guard = DeployGuard()
    guard_result = guard.evaluate()
    if not guard_result.allowed:
        print("[security-gate] Deploy blocked by environment guard:")
        for reason in guard_result.reasons:
            print(f"- {reason}")
        return 1

    gate = SecurityGate()
    report = gate.run()

    for check in report.reports:
        status = "OK" if check.allowed else "BLOCK"
        print(f"[security-gate] {check.name}: {status}")
        for issue in check.issues:
            loc = f" ({issue.location})" if issue.location else ""
            print(f"  - [{issue.severity}] {issue.category}: {issue.message}{loc}")

    if not report.allowed:
        print("[security-gate] Deployment blocked: high-risk vulnerabilities detected")
        return 1

    print("[security-gate] Deployment allowed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
