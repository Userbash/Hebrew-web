from __future__ import annotations
from typing import Any, Protocol, runtime_checkable
from datetime import datetime

@runtime_checkable
class MemoryProtocol(Protocol):
    """
    Standardized protocol for interacting with AI Orchestrator memory.
    Ensures consistent behavior across different storage backends.
    """
    
    def get(self, scope: str, identifier: str, key: str) -> Any | None:
        """Retrieve a specific memory value."""
        ...

    def set(self, scope: str, identifier: str, key: str, value: Any, ttl_sec: int | None = None) -> None:
        """Store a memory value with an optional TTL."""
        ...

    def list_keys(self, scope: str | None = None, identifier: str | None = None) -> list[str]:
        """List available memory keys in a given scope."""
        ...

    def load_from_cold_storage(self, path: str) -> int:
        """
        Batch load memories from a specified disk path.
        Returns the number of records loaded.
        """
        ...

    def save_to_cold_storage(self, path: str) -> None:
        """Force a dump of current memory to disk."""
        ...
