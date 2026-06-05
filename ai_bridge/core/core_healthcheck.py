from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass

from .agent_registry import AgentRegistry
from .env_loader import load_env_file
from .host_bridge import HostBridge
from .memory_backend import InMemoryBackend
from .memory_policy import MemoryPolicy
from .orchestrator import Orchestrator
from .session_memory import SessionMemory


@dataclass(slots=True)
class CheckResult:
    name: str
    ok: bool
    details: str


def _check_imports() -> CheckResult:
    modules = [
        "ai_bridge.core.orchestrator",
        "ai_bridge.core.models",
        "ai_bridge.core.session_memory",
        "ai_bridge.core.memory_backend",
        "ai_bridge.core.memory_policy",
        "ai_bridge.core.memory_invalidator",
        "ai_bridge.core.external_ai_bridge",
    ]
    failed: list[str] = []
    for module in modules:
        try:
            importlib.import_module(module)
        except Exception:
            failed.append(module)
    if failed:
        return CheckResult("imports", False, f"failed: {', '.join(failed)}")
    return CheckResult("imports", True, "all critical modules importable")


def _check_memory_backend() -> CheckResult:
    memory = SessionMemory()
    memory.set("health-session", "ping", "pong")
    ok = memory.get("health-session", "ping") == "pong"
    backend_ok = isinstance(memory.backend, InMemoryBackend)
    return CheckResult("memory_backend", bool(ok and backend_ok), "in-memory backend ready")


def _check_secret_redaction() -> CheckResult:
    memory = SessionMemory(policy=MemoryPolicy())
    memory.set("health-session", "secret", {"OPENAI_API_KEY": "sk-demo", "safe": "ok"})
    stored = memory.get("health-session", "secret")
    ok = stored["safe"] == "ok" and stored["OPENAI_API_KEY"] != "sk-demo"
    return CheckResult("secret_redaction", ok, "memory write path redacts sensitive keys")


def _check_agent_registry() -> CheckResult:
    registry = AgentRegistry()
    registry.register("health-agent", "custom", "local://health-agent", ["code"])
    ready = registry.ready_agents()
    ok = len(ready) == 1 and ready[0].id == "health-agent"
    return CheckResult("agent_registry", ok, "registry can register and resolve ready agents")


def _check_orchestrator_wiring() -> CheckResult:
    orchestrator = Orchestrator()
    ok = hasattr(orchestrator, "session_memory") and orchestrator.session_memory is not None
    return CheckResult("orchestrator_wiring", ok, "orchestrator has session memory wiring")


def _check_host_bridge() -> CheckResult:
    bridge = HostBridge()
    allowlist = bridge.allowlist()
    ok = len(allowlist) > 0
    return CheckResult("host_bridge", ok, f"host bridge mode={bridge.detect_mode()}")


def _check_container_provider() -> CheckResult:
    has_podman = shutil.which("podman") is not None
    has_docker = shutil.which("docker") is not None
    if has_podman or has_docker:
        return CheckResult("container_provider", True, "container runtime available")
    # Optional: external AI can work without container runtime.
    return CheckResult("container_provider", True, "optional runtime missing (no docker/podman in PATH)")


def _check_policy_config() -> CheckResult:
    policy = MemoryPolicy()
    ok = policy.max_entry_size > 0 and len(policy.denylist_keys) > 0
    return CheckResult("policy_config", ok, "memory policy loaded")


def _check_ai_provider_access() -> CheckResult:
    load_env_file()
    mistral_key = bool(os.getenv("MISTRAL_API_KEY"))

    from ai_bridge.core.availability import ModelAvailability

    gemini_cmd = ModelAvailability._resolve_gemini_cli_command()
    if gemini_cmd is not None:
        try:
            env = os.environ.copy()
            node_path = shutil.which("node")
            if not node_path:
                npx = shutil.which("npx")
                if npx:
                    node_dir = os.path.dirname(npx)
                    current_path = env.get("PATH", "")
                    if node_dir and node_dir not in current_path.split(os.pathsep):
                        env["PATH"] = f"{node_dir}{os.pathsep}{current_path}" if current_path else node_dir
            probe = subprocess.run([*gemini_cmd, "--version"], capture_output=True, text=True, timeout=25, check=False, env=env)
            gemini_cli_ok = probe.returncode == 0
        except Exception:
            gemini_cli_ok = False
    else:
        gemini_cli_ok = False

    if gemini_cli_ok or mistral_key:
        details = f"gemini_cli={gemini_cli_ok}, mistral_key={mistral_key}"
        return CheckResult("ai_provider_access", True, details)

    return CheckResult("ai_provider_access", False, "no external AI provider ready (gemini executable unavailable and MISTRAL_API_KEY missing)")


def run_healthcheck() -> tuple[bool, list[CheckResult]]:
    checks = [
        _check_imports(),
        _check_memory_backend(),
        _check_secret_redaction(),
        _check_agent_registry(),
        _check_orchestrator_wiring(),
        _check_host_bridge(),
        _check_container_provider(),
        _check_policy_config(),
        _check_ai_provider_access(),
    ]
    return all(item.ok for item in checks), checks


def main() -> int:
    ok, checks = run_healthcheck()
    payload = {
        "ok": ok,
        "checks": [asdict(item) for item in checks],
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
