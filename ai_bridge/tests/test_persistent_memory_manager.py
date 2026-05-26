from __future__ import annotations

import asyncio

from ai_bridge.core.memory_settings import MemorySettings
from ai_bridge.core.persistent_memory import PersistentMemoryManager


def test_non_uuid_session_is_normalized_and_stable() -> None:
    manager = PersistentMemoryManager(MemorySettings(enabled=False))

    first = asyncio.run(manager.upsert_session("task-abc", agent_id="agent-1"))
    second = asyncio.run(manager.upsert_session("task-abc", agent_id="agent-1"))

    assert first == second
    assert first != "task-abc"


def test_command_and_memory_are_isolated_by_agent() -> None:
    manager = PersistentMemoryManager(MemorySettings(enabled=False))

    asyncio.run(
        manager.store_memory(
            session_id="task-1",
            agent_id="agent-a",
            memory_type="episodic",
            content="A",
        )
    )
    asyncio.run(
        manager.store_memory(
            session_id="task-1",
            agent_id="agent-b",
            memory_type="episodic",
            content="B",
        )
    )

    a_rows = asyncio.run(manager.retrieve_memories(session_id="task-1", agent_id="agent-a", memory_type="episodic"))
    b_rows = asyncio.run(manager.retrieve_memories(session_id="task-1", agent_id="agent-b", memory_type="episodic"))

    assert len(a_rows) == 1
    assert len(b_rows) == 1
    assert a_rows[0].content == "A"
    assert b_rows[0].content == "B"
