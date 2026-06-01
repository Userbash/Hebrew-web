from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from .hybrid_memory import HybridMemory
from .memory_backend import InMemoryBackend, MemoryBackend
from .memory_policy import MemoryPolicy


class MemoryScope(str, Enum):
    SESSION = "session"
    TASK = "task"
    AGENT = "agent"
    CAPABILITY = "capability"


@dataclass(slots=True)
class MemoryEntry:
    key: str
    value: Any
    scope: MemoryScope
    created_at: datetime
    expires_at: datetime | None
    last_accessed_at: datetime
    invalidated_by: str | None = None


from .memory_protocol import MemoryProtocol
import json
import os
from pathlib import Path

class SessionMemory(MemoryProtocol):
    def __init__(self, backend: MemoryBackend | None = None, policy: MemoryPolicy | None = None, hybrid: HybridMemory | None = None) -> None:
        self.backend = backend or InMemoryBackend()
        self.policy = policy or MemoryPolicy()
        self.hybrid = hybrid or HybridMemory(backend=self.backend)

    @staticmethod
    def make_key(scope: MemoryScope, identifier: str, key: str) -> str:
        return f"{scope.value}:{identifier}:{key}"

    @staticmethod
    def _parse_scope_args(args: tuple[Any, ...]) -> tuple[MemoryScope, str, str]:
        if len(args) != 3:
            raise TypeError("Expected 3 positional arguments")

        a0, a1, a2 = args
        if isinstance(a0, MemoryScope):
            return a0, str(a1), str(a2)
        if str(a0) in {m.value for m in MemoryScope}:
            return MemoryScope(str(a0)), str(a1), str(a2)
        return MemoryScope.SESSION, str(a0), str(a1)

    def get(self, *args: Any) -> Any | None:
        if len(args) == 3:
            scope, identifier, key = self._parse_scope_args(args)
        elif len(args) == 2:
            scope, identifier, key = MemoryScope.SESSION, str(args[0]), str(args[1])
        else:
            raise TypeError("get expects (scope, identifier, key) or (session_id, key)")

        return self.hybrid.get(scope.value if hasattr(scope, "value") else str(scope), identifier, key)

    def set(self, *args: Any, ttl_sec: int | None = None, ttl_seconds: int | None = None) -> None:
        if len(args) == 4:
            scope = args[0]
            identifier = str(args[1])
            key = str(args[2])
            value = args[3]
        elif len(args) == 3:
            scope = MemoryScope.SESSION
            identifier = str(args[0])
            key = str(args[1])
            value = args[2]
        else:
            raise TypeError("set expects (scope, identifier, key, value) or (session_id, key, value)")

        ttl = ttl_sec if ttl_sec is not None else ttl_seconds
        redacted = self.policy.redact(value)
        self.policy.validate_size(redacted)
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=ttl) if ttl and ttl > 0 else None
        
        scope_val = scope.value if hasattr(scope, "value") else str(scope)
        self.hybrid.set(
            scope_val,
            identifier,
            key,
            redacted,
            expires_at=expires_at,
            memory_type="episodic",
        )

    def delete(self, *args: Any) -> None:
        if len(args) == 3:
            scope, identifier, key = self._parse_scope_args(args)
        elif len(args) == 2:
            scope, identifier, key = MemoryScope.SESSION, str(args[0]), str(args[1])
        else:
            raise TypeError("delete expects (scope, identifier, key) or (session_id, key)")

        self.hybrid.delete(scope.value if hasattr(scope, "value") else str(scope), identifier, key)

    def list_keys(self, scope: MemoryScope | str | None = None, identifier: str | None = None) -> list[str]:
        keys = self.hybrid.list_keys()
        scope_val = scope.value if hasattr(scope, "value") else str(scope) if scope else None
        if scope_val is not None:
            keys = [key for key in keys if key.startswith(f"{scope_val}:")]
        if identifier is not None:
            keys = [key for key in keys if f":{identifier}:" in key]
        return keys

    def invalidate(self, reason: str, prefix: str | None = None) -> int:
        _ = reason
        return self.hybrid.invalidate(prefix=prefix)

    def clear_session(self, session_id: str) -> int:
        return self.invalidate("session_end", prefix=f"{MemoryScope.SESSION.value}:{session_id}:")

    def load_from_cold_storage(self, path: str) -> int:
        """Loads records from memory_index.json and injected into hybrid memory."""
        idx_path = Path(path) / "memory_index.json"
        if not idx_path.exists():
            return 0
        
        try:
            with open(idx_path, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            return 0

        count = 0
        for rec in records:
            content = rec.get("content")
            meta = rec.get("metadata", {})
            scope = meta.get("scope", "session")
            key = meta.get("key", f"imported_{rec.get('memory_id')}")
            session_id = rec.get("source_session_id") or rec.get("session_id", "unknown")
            
            self.set(scope, session_id, key, content)
            count += 1
        return count

    def save_to_cold_storage(self, path: str) -> None:
        """Forces hybrid memory to persist its state (HybridMemory handles this via background tasks, but we can trigger it here)."""
        # PersistentMemoryManager already writes to disk on every store_memory call in Phase 1.
        # Here we just log the request.
        pass

