from __future__ import annotations

import asyncio
import importlib
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from ai_bridge.agents.mistral_agent import MistralAgent
from ai_bridge.core.agent_registry import AgentRegistry
from ai_bridge.core.models import Task, TaskContext, TaskInput, TaskType
from ai_bridge.core.orchestrator import Orchestrator
from ai_bridge.core.security import SecurityManager, SecurityPolicy


def check_modules() -> bool:
    print("[1/6] Checking Core Module Integrity...")
    modules = [
        "ai_bridge.core.orchestrator",
        "ai_bridge.core.agent_registry",
        "ai_bridge.core.host_bridge",
        "ai_bridge.agents.base_agent",
        "ai_bridge.protocols.rest_protocol",
    ]
    all_ok = True
    for mod in modules:
        try:
            importlib.import_module(mod)
            print(f"  ✅ {mod:.<40} OK")
        except ImportError as e:
            print(f"  ❌ {mod:.<40} FAILED ({e})")
            all_ok = False
    return all_ok


def check_env() -> bool:
    print("\n[2/6] Verifying Security Environment...")
    keys = ["MISTRAL_API_KEY"]
    all_ok = True
    for key in keys:
        val = os.getenv(key)
        if val:
            masked = val[:4] + "..." + val[-4:] if len(val) > 8 else "****"
            print(f"  ✅ {key:.<40} LOADED ({masked})")
        else:
            print(f"  ❌ {key:.<40} MISSING")
            all_ok = False
    return all_ok


def check_communication() -> bool:
    print("\n[3/6] Testing Module Communication (Registry <-> Orchestrator)...")
    try:
        registry = AgentRegistry()
        orchestrator = Orchestrator(registry=registry)

        from ai_bridge.agents.codex_agent import CodexAgent

        agent = CodexAgent("test-agent")
        orchestrator.attach_local_agent("test-agent", agent)

        retrieved = registry.get("test-agent")
        if retrieved and retrieved.id == "test-agent":
            print("  ✅ Registry Link.......................... OK")
        else:
            print("  ❌ Registry Link.......................... FAILED")
            return False

        if orchestrator.host_bridge:
            print("  ✅ Host Bridge Integration............... OK")
        else:
            print("  ❌ Host Bridge Integration............... FAILED")
            return False

        return True
    except Exception as e:
        print(f"  ❌ Communication Test FAILED: {e}")
        return False




def check_host_bridge_contract() -> bool:
    print("\n[4/7] Validating Host Bridge Integration...")
    try:
        from ai_bridge.core.host_bridge import HostBridge

        bridge = HostBridge()
        mode = bridge.detect_mode()
        allowlist = bridge.allowlist()

        if not allowlist:
            print("  ❌ Host Bridge Allowlist................. FAILED (empty)")
            return False

        # Validate at least one allowed command path on host.
        probes = [
            ["which", "node"],
            ["which", "podman"],
            ["which", "bash"],
        ]
        ok = False
        for cmd in probes:
            probe = bridge.execute(cmd, timeout=10, capture_output=True, text=True, check=False)
            if probe.returncode == 0:
                ok = True
                break

        if not ok:
            print(f"  ❌ Host Bridge Execute................... FAILED (mode={mode})")
            return False

        print(f"  ✅ Host Bridge Allowlist................. OK ({len(allowlist)} commands)")
        print(f"  ✅ Host Bridge Execute................... OK (mode={mode})")
        return True
    except Exception as e:
        print(f"  ❌ Host Bridge Contract FAILED: {e}")
        return False


def check_interface_contract() -> bool:
    print("\n[5/7] Validating Agent Interface Contract...")
    security_manager = SecurityManager(SecurityPolicy())
    mistral = MistralAgent("mistral-contract", security_manager)
    required_methods = ["run", "execute", "healthcheck"]

    missing = [method for method in required_methods if not hasattr(mistral, method)]
    if missing:
        print(f"  ❌ Interface Contract..................... FAILED (missing: {', '.join(missing)})")
        return False

    print("  ✅ Interface Contract..................... OK")
    return True


async def check_external_connectivity() -> bool:
    print("\n[6/7] Probing External AI Providers...")
    security_manager = SecurityManager(SecurityPolicy())

    mistral = MistralAgent("mistral-probe", security_manager)
    health = mistral.healthcheck()
    if health.status.value != "ready":
        print(f"  ❌ Mistral API (Configuration)............ FAILED ({health.last_error})")
        return False

    print("  ✅ Mistral API (Configuration)............ OK")
    try:
        task = Task(TaskType.CODE, TaskInput("say ping", []), TaskContext("probe", ".", "main"))
        result = mistral.execute(task)
        if result.status.value == "done":
            print("  ✅ Mistral API (Live Connectivity)........ OK")
            return True
        print(f"  ❌ Mistral API (Live Connectivity)........ FAILED ({result.output})")
        return False
    except Exception as e:
        print(f"  ❌ Mistral API (Live Connectivity)........ FAILED ({e})")
        return False


def check_filesystem() -> bool:
    print("\n[7/7] Checking Core Filesystem Hooks...")
    paths = [
        ".env",
        "ai_bridge/core/security_gate/authz.py",
        "scripts/bridge/exec.sh",
    ]
    all_ok = True
    for p in paths:
        if Path(p).exists():
            print(f"  ✅ {p:.<40} EXISTS")
        else:
            print(f"  ❌ {p:.<40} MISSING")
            all_ok = False
    return all_ok


async def main() -> int:
    print("=" * 60)
    print("AI BRIDGE CORE SYSTEM VERIFICATION")
    print("=" * 60)

    m_ok = check_modules()
    e_ok = check_env()
    c_ok = check_communication()
    h_ok = check_host_bridge_contract()
    i_ok = check_interface_contract()
    x_ok = await check_external_connectivity()
    f_ok = check_filesystem()

    overall_ok = all([m_ok, e_ok, c_ok, h_ok, i_ok, x_ok, f_ok])

    print("\n" + "=" * 60)
    if overall_ok:
        print("VERIFICATION COMPLETE: CORE SYSTEM IS HEALTHY")
    else:
        print("VERIFICATION COMPLETE: ISSUES DETECTED")
    print("=" * 60)
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
