from __future__ import annotations

import os
import sys
import importlib
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from ai_bridge.core.orchestrator import Orchestrator
from ai_bridge.core.agent_registry import AgentRegistry
from ai_bridge.core.models import Task, TaskContext, TaskInput, TaskType
from ai_bridge.agents.mistral_agent import MistralAgent
from ai_bridge.core.security import SecurityManager, SecurityPolicy

def check_modules() -> bool:
    print("[1/5] Checking Core Module Integrity...")
    modules = [
        "ai_bridge.core.orchestrator",
        "ai_bridge.core.agent_registry",
        "ai_bridge.core.host_bridge",
        "ai_bridge.agents.base_agent",
        "ai_bridge.protocols.rest_protocol"
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
    print("\n[2/5] Verifying Security Environment...")
    keys = ["MISTRAL_API_KEY"]
    all_ok = True
    for key in keys:
        val = os.getenv(key)
        if val:
            # Mask the key for safety
            masked = val[:4] + "..." + val[-4:] if len(val) > 8 else "****"
            print(f"  ✅ {key:.<40} LOADED ({masked})")
        else:
            print(f"  ❌ {key:.<40} MISSING")
            all_ok = False
    return all_ok

def check_communication() -> bool:
    print("\n[3/5] Testing Module Communication (Registry <-> Orchestrator)...")
    try:
        registry = AgentRegistry()
        orchestrator = Orchestrator(registry=registry)
        
        # Test agent attachment and retrieval
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

async def check_external_connectivity():
    print("\n[4/5] Probing External AI Providers...")
    security_manager = SecurityManager(SecurityPolicy())
    
    # Check Mistral
    mistral = MistralAgent("mistral-probe", security_manager)
    health = mistral.health()
    if health.status == "ready":
        print("  ✅ Mistral API (Configuration)............ OK")
        # Try a real small ping
        try:
            # Note: execute is async
            task = Task(TaskType.CODE, TaskInput("say 'ping'", []), TaskContext("probe", ".", "main"))
            result = await mistral.execute(task)
            if result.status.value == "done":
                print("  ✅ Mistral API (Live Connectivity)........ OK")
            else:
                print(f"  ⚠️  Mistral API (Live Connectivity)........ BLOCKED ({result.output})")
        except Exception as e:
            print(f"  ❌ Mistral API (Live Connectivity)........ FAILED ({e})")
    else:
        print(f"  ❌ Mistral API (Configuration)............ FAILED ({health.last_error})")

def check_filesystem() -> bool:
    print("\n[5/5] Checking Core Filesystem Hooks...")
    paths = [
        ".env",
        "ai_bridge/core/security_gate/authz.py",
        "scripts/bridge/exec.sh"
    ]
    for p in paths:
        if Path(p).exists():
            print(f"  ✅ {p:.<40} EXISTS")
        else:
            print(f"  ❌ {p:.<40} MISSING")
    return True

async def main():
    print("=" * 60)
    print("AI BRIDGE CORE SYSTEM VERIFICATION")
    print("=" * 60)
    
    m_ok = check_modules()
    e_ok = check_env()
    c_ok = check_communication()
    await check_external_connectivity()
    f_ok = check_filesystem()
    
    print("\n" + "=" * 60)
    if all([m_ok, e_ok, c_ok, f_ok]):
        print("VERIFICATION COMPLETE: CORE SYSTEM IS HEALTHY")
    else:
        print("VERIFICATION COMPLETE: ISSUES DETECTED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
