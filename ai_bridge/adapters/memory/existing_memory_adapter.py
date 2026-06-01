from __future__ import annotations
from typing import Any
from ai_bridge.core.session_memory import SessionMemory

class ExistingMemoryAdapter:
    def __init__(self, memory: SessionMemory) -> None:
        self.memory = memory
    def get(self, scope: str, owner_id: str, key: str) -> Any:
        if scope == "session":
            return self.memory.get(owner_id, key)
        return self.memory.get(scope, owner_id, key)
    def set(self, scope: str, owner_id: str, key: str, value: Any) -> None:
        if scope == "session":
            self.memory.set(owner_id, key, value)
            return
        self.memory.set(scope, owner_id, key, value)
