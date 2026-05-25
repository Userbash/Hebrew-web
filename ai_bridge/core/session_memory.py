from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from .memory_backend import BackendEntry, InMemoryBackend, MemoryBackend
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


class SessionMemory:
    def __init__(self, backend: MemoryBackend | None = None, policy: MemoryPolicy | None = None) -> None:
        self.backend = backend or InMemoryBackend()
        self.policy = policy or MemoryPolicy()

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

        # Backward-compatible short form: (session_id, key)
        # Used as SESSION scope implicitly.
        return MemoryScope.SESSION, str(a0), str(a1)

    def get(self, *args: Any) -> Any | None:
        if len(args) == 3 and isinstance(args[0], MemoryScope):
            scope, identifier, key = self._parse_scope_args(args)
        elif len(args) == 2:
            scope, identifier, key = MemoryScope.SESSION, str(args[0]), str(args[1])
        else:
            raise TypeError("get expects (scope, identifier, key) or (session_id, key)")

        entry = self.backend.get(self.make_key(scope, identifier, key))
        return None if entry is None else entry.value

    def set(self, *args: Any, ttl_sec: int | None = None, ttl_seconds: int | None = None) -> None:
        if len(args) == 4 and isinstance(args[0], MemoryScope):
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
        self.backend.set(
            self.make_key(scope, identifier, key),
            BackendEntry(value=redacted, created_at=now, expires_at=expires_at, last_accessed_at=now),
        )

    def delete(self, *args: Any) -> None:
        if len(args) == 3 and isinstance(args[0], MemoryScope):
            scope, identifier, key = self._parse_scope_args(args)
        elif len(args) == 2:
            scope, identifier, key = MemoryScope.SESSION, str(args[0]), str(args[1])
        else:
            raise TypeError("delete expects (scope, identifier, key) or (session_id, key)")

        self.backend.delete(self.make_key(scope, identifier, key))

    def list_keys(self, scope: MemoryScope | None = None, identifier: str | None = None) -> list[str]:
        keys = list(self.backend.keys())
        if scope is not None:
            keys = [key for key in keys if key.startswith(f"{scope.value}:")]
        if identifier is not None:
            keys = [key for key in keys if f":{identifier}:" in key]
        return keys

    def invalidate(self, reason: str, prefix: str | None = None) -> int:
        removed = 0
        for key in list(self.backend.keys()):
            if prefix and not key.startswith(prefix):
                continue
            entry = self.backend.get(key)
            if entry is not None:
                entry.invalidated_by = reason
            self.backend.delete(key)
            removed += 1
        return removed

    def clear_session(self, session_id: str) -> int:
        return self.invalidate("session_end", prefix=f"{MemoryScope.SESSION.value}:{session_id}:")
