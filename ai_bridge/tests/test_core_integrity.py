"""
Core integrity tests for AI Bridge.

These tests verify that the core runtime is wired correctly:
- critical modules are importable;
- execution envelope exposes memory fields;
- session memory contract works;
- secret redaction is enforced;
- agents accept memory_context.
"""

from __future__ import annotations

import inspect
import time


def test_core_modules_importable():
    import ai_bridge.core.memory_backend  # noqa: F401
    import ai_bridge.core.memory_invalidator  # noqa: F401
    import ai_bridge.core.memory_policy  # noqa: F401
    import ai_bridge.core.models  # noqa: F401
    import ai_bridge.core.orchestrator  # noqa: F401
    import ai_bridge.core.host_bridge  # noqa: F401
    import ai_bridge.core.distrobox_bridge  # noqa: F401
    import ai_bridge.core.gh_auth_bridge  # noqa: F401
    import ai_bridge.core.kernel_module_manager  # noqa: F401
    import ai_bridge.core.ai_activity_module  # noqa: F401
    import ai_bridge.core.session_memory  # noqa: F401


def test_execution_envelope_has_memory_fields():
    from ai_bridge.core.models import Task

    fields = getattr(Task, "__dataclass_fields__", {})

    expected = {
        "session_id",
        "memory_scope",
        "memory_keys",
        "memory_ttl_sec",
        "cache_policy",
        "repo_fingerprint",
    }

    missing = expected - set(fields.keys())
    assert not missing, f"Missing memory fields: {missing}"


def test_session_memory_basic_contract():
    from ai_bridge.core.session_memory import SessionMemory

    memory = SessionMemory()
    memory.set("session-1", "project_tree", {"files": ["main.py"]})

    assert memory.get("session-1", "project_tree") == {"files": ["main.py"]}

    memory.delete("session-1", "project_tree")
    assert memory.get("session-1", "project_tree") is None

    memory.set("session-1", "x", "value")
    memory.clear_session("session-1")
    assert memory.get("session-1", "x") is None


def test_session_memory_ttl_expiry():
    from ai_bridge.core.session_memory import SessionMemory

    memory = SessionMemory()
    memory.set("session-1", "short", "value", ttl_seconds=1)

    assert memory.get("session-1", "short") == "value"

    time.sleep(1.1)

    assert memory.get("session-1", "short") is None


def test_memory_redacts_secrets_before_write():
    from ai_bridge.core.session_memory import SessionMemory

    memory = SessionMemory()
    memory.set(
        "session-1",
        "env",
        {
            "OPENAI_API_KEY": "sk-test-secret",
            "normal_value": "safe",
        },
    )

    stored = memory.get("session-1", "env")

    assert stored["normal_value"] == "safe"
    assert stored["OPENAI_API_KEY"] != "sk-test-secret"
    assert "sk-test-secret" not in str(stored)


def test_base_agent_run_accepts_memory_context():
    from ai_bridge.agents.base_agent import BaseAgent

    signature = inspect.signature(BaseAgent.run)
    assert "memory_context" in signature.parameters


def test_local_agents_accept_memory_context():
    agent_imports = [
        ("ai_bridge.agents.codex_agent", "CodexAgent"),
        ("ai_bridge.agents.tester_agent", "TesterAgent"),
        ("ai_bridge.agents.reviewer_agent", "ReviewerAgent"),
        ("ai_bridge.agents.docs_agent", "DocsAgent"),
        ("ai_bridge.agents.planner_agent", "PlannerAgent"),
    ]

    for module_name, class_name in agent_imports:
        try:
            module = __import__(module_name, fromlist=[class_name])
            agent_cls = getattr(module, class_name)
        except (ImportError, AttributeError):
            continue

        signature = inspect.signature(agent_cls.run)
        assert "memory_context" in signature.parameters, (
            f"{class_name}.run must accept memory_context"
        )
