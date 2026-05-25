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
    print("[1/8] Checking Core Module Integrity...")
    modules = [
        "ai_bridge.core.orchestrator",
        "ai_bridge.core.agent_registry",
        "ai_bridge.core.host_bridge",
        "ai_bridge.core.distrobox_bridge",
        "ai_bridge.core.gh_auth_bridge",
        "ai_bridge.core.kernel_module_manager",
        "ai_bridge.core.ai_activity_module",
        "ai_bridge.agents.base_agent",
        "ai_bridge.protocols.rest_protocol",
    ]
    all_ok = True
    for mod in modules:
        try:
            importlib.import_module(mod)
            print(f"  ✅ {mod:.<40} OK")
        except ImportError as exc:
            print(f"  ❌ {mod:.<40} FAILED ({exc})")
            all_ok = False
    return all_ok


def check_env() -> bool:
    print("\n[2/8] Verifying Security Environment...")
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
    print("\n[3/8] Testing Module Communication (Registry <-> Orchestrator)...")
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
    except Exception as exc:
        print(f"  ❌ Communication Test FAILED: {exc}")
        return False


def check_orchestrator_consistency() -> bool:
    print("\n[4/8] Validating Orchestrator Consistency...")
    try:
        orchestrator = Orchestrator()

        required_components = {
            "registry": orchestrator.registry,
            "router": orchestrator.router,
            "scheduler": orchestrator.scheduler,
            "host_bridge": orchestrator.host_bridge,
            "module_manager": orchestrator.module_manager,
            "session_memory": orchestrator.session_memory,
            "availability": orchestrator.availability,
        }

        missing = [name for name, ref in required_components.items() if ref is None]
        if missing:
            print(f"  ❌ Required Components................... FAILED (missing: {', '.join(missing)})")
            return False

        if orchestrator.router.registry is not orchestrator.registry:
            print("  ❌ Router/Registry Wiring................ FAILED")
            return False

        loaded = orchestrator.loaded_kernel_modules()
        unloaded = sorted(set(orchestrator.module_manager._modules.keys()) - set(loaded))
        print(f"  ✅ Kernel Modules Loaded................. {loaded}")
        print(f"  ✅ Kernel Modules Unloaded............... {unloaded}")

        if "ai_activity" not in loaded:
            print("  ❌ ai_activity Autoload.................. FAILED")
            return False

        orchestrator.unload_kernel_module("ai_activity")
        if "ai_activity" in orchestrator.loaded_kernel_modules():
            print("  ❌ Kernel Unload (ai_activity)........... FAILED")
            return False

        orchestrator.load_kernel_module("ai_activity")
        if "ai_activity" not in orchestrator.loaded_kernel_modules():
            print("  ❌ Kernel Load (ai_activity)............. FAILED")
            return False

        print("  ✅ Orchestrator Wiring................... OK")
        print("  ✅ Kernel Load/Unload Cycle.............. OK")
        return True
    except Exception as exc:
        print(f"  ❌ Orchestrator Consistency FAILED: {exc}")
        return False


def check_host_bridge_contract() -> bool:
    print("\n[5/8] Validating Host Bridge Integration...")
    try:
        from ai_bridge.core.host_bridge import HostBridge

        bridge = HostBridge()
        mode = bridge.detect_mode()
        allowlist = bridge.allowlist()

        if not allowlist:
            print("  ❌ Host Bridge Allowlist................. FAILED (empty)")
            return False

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
    except Exception as exc:
        print(f"  ❌ Host Bridge Contract FAILED: {exc}")
        return False


def check_interface_contract() -> bool:
    print("\n[6/8] Validating Agent Interface Contract...")
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
    print("\n[7/8] Probing External AI Providers...")
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
    except Exception as exc:
        print(f"  ❌ Mistral API (Live Connectivity)........ FAILED ({exc})")
        return False


def check_filesystem() -> bool:
    print("\n[8/8] Checking Core Filesystem Hooks...")
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
    o_ok = check_orchestrator_consistency()
    h_ok = check_host_bridge_contract()
    i_ok = check_interface_contract()
    x_ok = await check_external_connectivity()
    f_ok = check_filesystem()

    overall_ok = all([m_ok, e_ok, c_ok, o_ok, h_ok, i_ok, x_ok, f_ok])

    print("\n" + "=" * 60)
    if overall_ok:
        print("VERIFICATION COMPLETE: CORE SYSTEM IS HEALTHY")
    else:
        print("VERIFICATION COMPLETE: ISSUES DETECTED")
    print("=" * 60)
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
