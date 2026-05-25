from __future__ import annotations

import time

from ai_bridge.core.session_memory import MemoryScope, SessionMemory


def test_session_memory_set_get_delete_cycle():
    memory = SessionMemory()
    memory.set(MemoryScope.SESSION, "s1", "project_tree", {"files": ["a.py"]})

    assert memory.get(MemoryScope.SESSION, "s1", "project_tree") == {"files": ["a.py"]}

    memory.delete(MemoryScope.SESSION, "s1", "project_tree")
    assert memory.get(MemoryScope.SESSION, "s1", "project_tree") is None


def test_session_memory_ttl_expiration():
    memory = SessionMemory()
    memory.set(MemoryScope.TASK, "t1", "tmp", {"ok": True}, ttl_sec=1)
    assert memory.get(MemoryScope.TASK, "t1", "tmp") == {"ok": True}

    time.sleep(1.1)
    assert memory.get(MemoryScope.TASK, "t1", "tmp") is None


def test_session_memory_invalidate_prefix():
    memory = SessionMemory()
    memory.set(MemoryScope.SESSION, "s1", "k1", 1)
    memory.set(MemoryScope.SESSION, "s1", "k2", 2)
    memory.set(MemoryScope.SESSION, "s2", "k3", 3)

    removed = memory.clear_session("s1")
    assert removed == 2
    assert memory.get(MemoryScope.SESSION, "s1", "k1") is None
    assert memory.get(MemoryScope.SESSION, "s2", "k3") == 3
