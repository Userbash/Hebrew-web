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
        diagnostics = getattr(health, "diagnostics", {}) or {}
        tcp = diagnostics.get("tcp", {}) if isinstance(diagnostics, dict) else {}
        if tcp:
            print(f"  TCP reachable: {tcp.get('ok')}")
            for target in tcp.get("targets", []):
                status = "ok" if target.get("ok") else target.get("error_type", "failed")
                endpoint = f"{target.get('host')}:{target.get('port')}"
                latency = target.get("latency_ms")
                suffix = f" ({latency:.1f}ms)" if isinstance(latency, (int, float)) else ""
                print(f"    - {endpoint}: {status}{suffix}")
        api_probe = diagnostics.get("api_probe", {}) if isinstance(diagnostics, dict) else {}
        if api_probe:
            print(f"  API status_code: {api_probe.get('status_code')}")
        model_probe = diagnostics.get("model_probe", {}) if isinstance(diagnostics, dict) else {}
        if model_probe:
            print(f"  Model probe: {model_probe.get('command')} model={model_probe.get('model')} returncode={model_probe.get('returncode')}")
        for step in diagnostics.get("remediation", []) if isinstance(diagnostics, dict) else []:
            print(f"  Fix: {step}")

    print("\n--- Agent Health ---")
    for health in checker.check_all():
        print(health.as_dict())

if __name__ == "__main__":
    main()
