from __future__ import annotations

import pytest

from ai_bridge.core.memory_policy import MemoryPolicy
from ai_bridge.core.session_memory import MemoryScope, SessionMemory


def test_memory_redacts_sensitive_keys():
    memory = SessionMemory(policy=MemoryPolicy())
    payload = {
        "api_key": "secret-key",
        "nested": {"refresh_token": "token-value", "safe": "x"},
    }

    memory.set(MemoryScope.SESSION, "s1", "security_findings", payload)
    stored = memory.get(MemoryScope.SESSION, "s1", "security_findings")

    assert stored["api_key"] == "[REDACTED]"
    assert stored["nested"]["refresh_token"] == "[REDACTED]"
    assert stored["nested"]["safe"] == "x"


def test_memory_rejects_oversized_entries():
    policy = MemoryPolicy(max_entry_size=16)
    memory = SessionMemory(policy=policy)

    with pytest.raises(ValueError):
        memory.set(MemoryScope.TASK, "t1", "huge", {"data": "x" * 100})
