from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class BackendEntry:
    value: Any
    created_at: datetime
    expires_at: datetime | None
    last_accessed_at: datetime
    invalidated_by: str | None = None


class MemoryBackend(ABC):
    @abstractmethod
    def get(self, key: str) -> BackendEntry | None:
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, entry: BackendEntry) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def keys(self) -> Iterable[str]:
        raise NotImplementedError

    @abstractmethod
    def keys_by_prefix(self, prefix: str) -> Iterable[str]:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError


class InMemoryBackend(MemoryBackend):
    def __init__(self) -> None:
        self._store: dict[str, BackendEntry] = {}

    def get(self, key: str) -> BackendEntry | None:
        entry = self._store.get(key)
        if not entry:
            return None
        if entry.expires_at and datetime.now(UTC) >= entry.expires_at:
            self._store.pop(key, None)
            return None
        entry.last_accessed_at = datetime.now(UTC)
        return entry

    def set(self, key: str, entry: BackendEntry) -> None:
        self._store[key] = entry

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def keys(self) -> Iterable[str]:
        return list(self._store.keys())

    def keys_by_prefix(self, prefix: str) -> Iterable[str]:
        return [key for key in self._store.keys() if key.startswith(prefix)]

    def clear(self) -> None:
        self._store.clear()
