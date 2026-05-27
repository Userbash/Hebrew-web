from __future__ import annotations

from ai_bridge.core.hybrid_memory import HybridMemory
from ai_bridge.core.memory_settings import MemorySettings


def test_hybrid_memory_eviction_and_restore_from_persistent():
    settings = MemorySettings(hot_cache_max_entries=3, retrieval_top_k=10)
    memory = HybridMemory(settings=settings)

    memory.set("session", "s1", "k1", {"v": 1}, importance_score=0.1)
    memory.set("session", "s1", "k2", {"v": 2}, importance_score=0.9)
    memory.set("session", "s1", "k3", {"v": 3}, importance_score=0.8)
    memory.set("session", "s1", "k4", {"v": 4}, importance_score=0.7)

    evicted = memory.run_maintenance_once()
    assert evicted >= 1

    restored = memory.get("session", "s1", "k1")
    assert restored is not None
    assert "v" in str(restored)


def test_hybrid_memory_command_window_roundtrip():
    memory = HybridMemory()
    memory.remember_command(
        session_id="sess-1",
        agent_id="agent-1",
        command="task:code",
        result={"summary": "ok", "status": "done"},
        success=True,
        tokens_used=111,
    )
    window = memory.load_command_window(session_id="sess-1", agent_id="agent-1", limit=5)
    assert len(window) == 1
    assert window[0]["command"] == "task:code"


def test_hybrid_memory_key_taxonomy_for_thoughts_and_cleanup():
    memory = HybridMemory()
    memory.append_agent_thought(session_id="s-1", agent_id="a-1", thought="step-1")
    memory.append_agent_error(session_id="s-1", agent_id="a-1", error="boom")

    thought_key = memory.session_agent_thoughts_key("s-1", "a-1")
    error_key = memory.session_agent_errors_key("s-1", "a-1")

    assert memory.get_by_full_key(thought_key) == ["step-1"]
    assert memory.get_by_full_key(error_key) == ["boom"]

    removed = memory.clear_session_thoughts(session_id="s-1")
    assert removed == 2
    assert memory.get_by_full_key(thought_key) is None


def test_hybrid_memory_fast_retrieve_weighted_scoring():
    memory = HybridMemory()
    memory.set_by_full_key("session:s2:state", {"objective": "Implement login API"}, importance_score=0.6)
    memory.set_by_full_key("memory:domain:hebrew-web:patterns", "Use JWT middleware for login", importance_score=0.9)
    memory.set_by_full_key("task:t1:artifacts:diff", "Refactor CSS", importance_score=0.2)

    hits = memory.fast_retrieve(query_text="login jwt api", project_name="hebrew-web", top_k=2)
    assert len(hits) >= 1
    assert hits[0].score >= 0.0
    assert "memory:domain:hebrew-web:patterns" in hits[0].key

    brief = memory.build_context_brief(hits=hits, token_limit=50)
    assert "memory:domain:hebrew-web:patterns" in brief


def test_hybrid_memory_restore_by_key_ignores_top_k_window():
    settings = MemorySettings(hot_cache_max_entries=2, retrieval_top_k=1)
    memory = HybridMemory(settings=settings)

    memory.set("session", "s-index", "target", {"v": "old"}, importance_score=0.1)
    memory.set("session", "s-index", "newer-1", {"v": 1}, importance_score=0.9)
    memory.set("session", "s-index", "newer-2", {"v": 2}, importance_score=0.9)

    memory.run_maintenance_once()
    memory.delete("session", "s-index", "target")

    restored = memory.get("session", "s-index", "target")
    assert restored is not None
    assert "old" in str(restored)
