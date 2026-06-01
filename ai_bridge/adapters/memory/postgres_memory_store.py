from __future__ import annotations
import os
from typing import Any
from ai_bridge.core.session_memory import SessionMemory

class PostgresMemoryShadowStore:
    def __init__(self, existing: SessionMemory) -> None:
        self.enabled = os.getenv("AI_BRIDGE_ENABLE_POSTGRES_STATE", "false").lower() in {"1","true","yes","on"}
        self.existing = existing
        self.shadow_writes: list[dict[str, Any]] = []

    def get(self, scope: str, owner_id: str, key: str) -> Any:
        if scope == "session":
            return self.existing.get(owner_id, key)
        return self.existing.get(scope, owner_id, key)

    def set(self, scope: str, owner_id: str, key: str, value: Any) -> None:
        if scope == "session":
            self.existing.set(owner_id, key, value)
        else:
            self.existing.set(scope, owner_id, key, value)
        if self.enabled:
            self.shadow_writes.append({"scope": scope, "owner_id": owner_id, "key": key, "value": value})
